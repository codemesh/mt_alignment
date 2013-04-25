import sys

WORD_NULL = '__NULL__'

class param_table:
    """The parameter table for EM algo.
    
    It has the following members.
    - t The dict containing t[f][e] = t(f|e)
    - c The dict containing c[f][e] = c(e, f)
    - c_e c_e[e] = c(e)
    - q The dict containing q[l-m-i][j] = q(j|i, l, m)
    - c_ij The dict containing c_ij[l-m-i][j] = c(j|i, l, m)
    - c_ilm The dict containint c_ilm[l-m-i] = c(i, l, m)
    """

    def __init__(self):
        self.t = dict()
        self.c = dict()
        self.c_e = dict()
        self.q = dict()
        self.c_ij = dict()
        self.c_ilm = dict()

    def load_param_t(self, t_stream):
        for line in t_stream:
            line.rstrip()
            e_f_t = line.split()
            e = e_f_t[0]
            f = e_f_t[1]
            t = float(e_f_t[2])
            if not f in self.t:
                self.t[f] = dict()
            self.t[f][e] = t

            if not f in self.c:
                self.c[f] = dict()
            self.c[f][e] = 0.0
            self.c_e[e] = 0.0

    def extract_key(self, k):
        i, l, m = k.split('-')
        return int(i), int(l), int(m)

    def get_q_key(self, i, l, m):
        return '%d-%d-%d' % (i, l, m)
    
    def update_param_q(self, m, l):
        """Update parameter q with a sentence length pair.

        Param l is the length of the target language(e language), including the added NULL
        Param m is the length of the source language(f language).
        """
        for i in range(m):
            i += 1
            # l - 1 to get rid of leading NULL
            k = self.get_q_key(i, l - 1, m)
            if k in self.q:
                return
            self.q[k] = list()
            self.c_ij[k] = list()
            self.c_ilm[k] = 0.0
            q = 1 / float(l)
            for j in range(l):
                self.q[k].append(q)
                self.c_ij[k].append(0.0)
                

    def update_with_sentence(self, f_words, e_words):
        l = len(e_words)
        m = len(f_words)
        for i in range(m):
            f = f_words[i]
            i += 1
            k = self.get_q_key(i, l - 1, m)
            count_total = 0.0
            for j in range(l):
                e = e_words[j]
                q = self.q[k][j]
                if not e in self.t[f]:
                    self.t[f][e] = 0.0
                t = self.t[f][e]
                count_total += q * t
            for j in range(l):
                e = e_words[j]
                delta = self.q[k][j] * self.t[f][e] / count_total
                if not e in self.c[f]:
                    self.c[f][e] = 0.0
                self.c[f][e] += delta
                self.c_e[e] += delta
                self.c_ij[k][j] += delta
                self.c_ilm[k] += delta

    def end_round(self):
        for f in self.t:
            for e in self.t[f]:
                self.t[f][e] = self.c[f][e] / self.c_e[e]

        for k in self.c_ij:
            for j, c in enumerate(self.c_ij[k]):
                self.q[k][j] = c / self.c_ilm[k]

        for e in self.c_e:
            self.c_e[e] = 0.0
        for f in self.c:
            for e in self.c[f]:
                self.c[f][e] = 0.0

        for k in self.c_ilm:
            self.c_ilm[k] = 0.0
        for k in self.c_ij:
            for j, c in enumerate(self.c_ij[k]):
                self.c_ij[k][j] = 0.0

    def output(self, stream):
        for f in self.t:
            for e in self.t[f]:
                if self.t[f][e] <= 1e-6 and e != WORD_NULL:
                    continue
                stream.write('t %s %s %f\n' % (e, f, self.t[f][e]))

        for k in self.q:
            i, l, m = self.extract_key(k)
            for j, q in enumerate(self.q[k]):
                if q <= 1e-6 and j != 0:
                    continue
                stream.write('q %d %d %d %d %f\n' % (j, i, l, m, q))

def build_param_table(t_stream, source_stream, target_stream):
    t = param_table()
    t.load_param_t(t_stream)
    for source in source_stream:
        source.rstrip()
        target = target_stream.readline()
        target.rstrip()
        source_words = source.split()
        target_words = target.split()
        target_words.insert(0, WORD_NULL)
        t.update_param_q(len(source_words), len(target_words))
        
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
        target_words.insert(0, WORD_NULL)

        t.update_with_sentence(source_words, target_words)

    t.end_round()

def estimate_t_q(t_stream, source_stream, target_stream, round_count):
    t = build_param_table(t_stream, source_stream, target_stream)

    for i in range(round_count):
        iterate_one_round(source_stream, target_stream, t)
    return t

def estimate_from_file(tfile, source, target, round_count):
    with open(source) as source_stream:
        with open(target) as target_stream:
            with open(tfile) as t_stream:
                t = estimate_t_q(t_stream, source_stream, target_stream, round_count)

        t.output(sys.stdout)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print 'usage: %s t_file, e_file f_file' % sys.argv[0]
        sys.exit(1)
    
    estimate_from_file(sys.argv[1], sys.argv[3], sys.argv[2], 5)
