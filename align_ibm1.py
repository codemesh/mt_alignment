import sys

WORD_NULL = '__NULL__'

def align_sentence(t, source_words, target_words):
    """Align a source-target sentence pair.

    t is the param t, which is a dict whose key is the foreign/source word
    f and whose value is dict of pairs of {english/target word e => t(f|e)}
    """
    alignment = []
    for f in source_words:
        t_of_f = t[f]
        max_t_seen = 0.0
        alignment_of_f = 0
        e_index = 0
        for e in target_words:
            e_index += 1
            if not e in t_of_f:
                continue
            t_of_f_e = t_of_f[e]
            if t_of_f_e >= max_t_seen:
                max_t_seen = t_of_f_e
                alignment_of_f = e_index
                
        alignment.append(alignment_of_f)

    return alignment

def align_sentences(t, source_stream, target_stream, output_stream):
    sentence_index = 0
    for source in source_stream:
        source.rstrip()
        target = target_stream.readline()
        target.rstrip()
        sentence_index += 1
        source_words = source.split()
        target_words = target.split()
        target_words.append(WORD_NULL)
        alignment = align_sentence(t, source_words, target_words)
        
        word_index = 0
        for a in alignment:
            word_index += 1
            output_stream.write('%d %d %d\n' %(
                    sentence_index, a, word_index))

def align_files(t, source_file, target_file, output_stream):
    with open(source_file) as source_stream:
        with open(target_file) as target_stream:
            align_sentences(t, source_stream, target_stream, output_stream)

def load_t(t_stream):
    """Load the t parameter into memory.

    t is a dict whose key is a foreign word f, whose value is a
    dict of {e => t(f|e)} where e is an english word.
    """
    t = dict()
    for line in t_stream:
        line.rstrip()
        e_f_t = line.split()
        if not e_f_t[1] in t:
            t[e_f_t[1]] = dict()
        t[e_f_t[1]][e_f_t[0]] = float(e_f_t[2])

    return t

def load_t_from_file(t_file):
    with open(t_file) as t_stream:
        t = load_t(t_stream)

    return t
            
def load_and_align(t_file, source_file, target_file, output_stream):
    t = load_t_from_file(t_file)
    align_files(t, source_file, target_file, output_stream)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print 'usage: %s t_file e_file, f_file' % sys.argv[0]
        sys.exit(1)

    load_and_align(sys.argv[1], sys.argv[3], sys.argv[2], sys.stdout)
