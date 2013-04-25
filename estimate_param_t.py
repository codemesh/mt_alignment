import sys

WORD_NULL = '__NULL__'

class target_word:
    """A target word e in the parameter t(f|e)
    
    A target word 'e' has the following members:
    - c(e)
    - a c dict whose entries are c(e, f) for different f's
      - f -> c(e, f)
    - a t dict whose entries are t(f|e) for different f's
      - f -> t(f|e)
    - sum of t(f|e)
    """

    def __init__(self):
        self.c_e = 0.0
        self.c = dict()
        self.t = dict()
        self.sum_of_t = 0.0
        
    def init_with_fs(self, fs):
        """Init with f's

        fs is a set of all f's
        """
        num_of_fs = len(fs)
        for f in fs:
            self.c[f] = 0
            self.t[f] = 1 / float(num_of_fs)

        self.sum_of_t = 1.0
        return self
    
    def update_source_word(self, f):
        # note, delta(e, f) can be pre-calculated
        delta = self.t[f] / self.sum_of_t
        self.c[f] += delta
        self.c_e += delta

    def end_round(self):
        self.sum_of_t = 0.0
        for f in self.c:
            self.t[f] = self.c[f] / self.c_e
            self.sum_of_t += self.t[f]

class param_table:
    """The parameter table for EM algo.
    
    It has the following members.
    - t The dict containing t[f][e] = t(f|e)
    - c The dict containing c[f][e] = c(e, f)
    - c_e c_e[e] = c(e)
    """

    def __init__(self):
        self.t = dict()
        self.c = dict()
        self.c_e = dict()

    def init_with_alignments(self, alignments):
        """Init the params with alignments.
        
        Alignments is all the possible alignments from the training bitext
        each entry of alignments is a pair whose key is a target word e
        and whose value is a list containing all the source words f to
        which e can be aligned with. So the layout looks like:
        e1 => [f11, f12, f13]
        e2 => [f21, f22]
        ...
        """
        for e in alignments:
            self.c_e[e] = 0.0
            fs = alignments[e]
            num_of_fs = len(fs)
            for f in fs:
                if not f in self.t:
                    self.t[f] = dict()
                self.t[f][e] = 1 / float(num_of_fs)
                if not f in self.c:
                    self.c[f] = dict()
                self.c[f][e] = 0.0

    def update_with_sentence(self, f_words, e_words):
        for f in f_words:
            sum_of_t_f_e = 0
            for e in e_words:
                sum_of_t_f_e += self.t[f][e]
            for e in e_words:
                delta = self.t[f][e] / sum_of_t_f_e
                self.c[f][e] += delta
                self.c_e[e] += delta

    def end_round(self):
        for f in self.t:
            for e in self.t[f]:
                self.t[f][e] = self.c[f][e] / self.c_e[e]

        for e in self.c_e:
            self.c_e[e] = 0.0
        for f in self.c:
            for e in self.c[f]:
                self.c[f][e] = 0.0

    def output(self, stream):
        for f in self.t:
            for e in self.t[f]:
                if self.t[f][e] <= 1e-6 and e != WORD_NULL:
                    continue
                stream.write('%s %s %f\n' % (e, f, self.t[f][e]))

def build_pair(source_stream, target_stream):
    e = dict()
    for source in source_stream:
        source.rstrip()
        target = target_stream.readline()
        target.rstrip()
        source_words = source.split()
        target_words = target.split()
        target_words.append(WORD_NULL)
        
        for target_word in target_words:
            if not target_word in e:
                e[target_word] = set()
            for source_word in source_words:
                e[target_word].add(source_word)

    return e

def build_param_table(source_stream, target_stream):
    t = param_table()
    word_pairs = build_pair(source_stream, target_stream)
    t.init_with_alignments(word_pairs)
    return t

def iterate_one_round(source_stream, target_stream, t):
    source_stream.seek(0)
    target_stream.seek(0)
    for source in source_stream:
        source.rstrip()
        target = target_stream.readline()
        target.rstrip()
        source_words = source.split()
        target_words = target.split()
        target_words.append(WORD_NULL)

        t.update_with_sentence(source_words, target_words)

    t.end_round()

def estimate_t(source_stream, target_stream, round_count):
    t = build_param_table(source_stream, target_stream)

    for i in range(round_count):
        iterate_one_round(source_stream, target_stream, t)
    return t

def output_t(target_word_table, output_stream):
    for f in target_word_table:
        target_word_info = target_word_table[e]
        for f in target_word_info.t:
            output_stream.write('%s %s %f\n' % (
                    e, f, target_word_info.t[f]))
    
def estimate_from_file(source, target, round_count):
    with open(source) as source_stream:
        with open(target) as target_stream:
            t = estimate_t(source_stream, target_stream, round_count)

        t.output(sys.stdout)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'usage: %s e_file f_file' % sys.argv[0]
        sys.exit(1)
    
    estimate_from_file(sys.argv[2], sys.argv[1], 5)
