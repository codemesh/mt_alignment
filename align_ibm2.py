import sys

WORD_NULL = '__NULL__'

def get_ilm_key(i, l, m):
    return '%d-%d-%d' % (i, l, m)

def align_sentence(t, q, source_words, target_words):
    alignment = []
    l = len(target_words)
    m = len(source_words)
    for i, f in enumerate(source_words):
        i += 1
        # l - 1 to get rid of NULL at index 0
        k = get_ilm_key(i, l - 1, m)
        t_of_f = t[f]
        q_of_i = q[k]
        max_score = 0.0
        alignment_of_f = 0
        for j, e in enumerate(target_words):
            if not e in t_of_f:
                continue
            t_of_f_e = t_of_f[e]
            q_of_i_j = q_of_i[j]
            score = t_of_f_e * q_of_i_j
            if score >= max_score:
                max_score = score
                alignment_of_f = j
        
        alignment.append(alignment_of_f)

    return alignment

def align_sentences(t, q, source_stream, target_stream, output_stream):
    sentence_index = 0
    for source in source_stream:
        source.rstrip()
        target = target_stream.readline()
        target.rstrip()
        sentence_index += 1
        source_words = source.split()
        target_words = target.split()
        target_words.insert(0, WORD_NULL)
        alignment = align_sentence(t, q, source_words, target_words)
        
        word_index = 0
        for a in alignment:
            word_index += 1
            output_stream.write('%d %d %d\n' %(
                    sentence_index, a, word_index))

def align_files(t, q, source_file, target_file, output_stream):
    with open(source_file) as source_stream:
        with open(target_file) as target_stream:
            align_sentences(t, q, source_stream, target_stream, output_stream)

def load_t_q(t_stream):
    """Load the t parameter into memory.

    t is a dict whose key is a foreign word f, whose value is a
    dict of {e => t(f|e)} where e is an english word.
    """
    t = dict()
    q = dict()
    for line in t_stream:
        line.rstrip()
        fields = line.split()
        if fields[0] == 't':
            e = fields[1]
            f = fields[2]
            t_of_f_e = float(fields[3])
            if not f in t:
                t[f] = dict()
            t[f][e] = t_of_f_e
        else:
            j = int(fields[1])
            i = int(fields[2])
            l = int(fields[3])
            m = int(fields[4])
            q_of_i_j = float(fields[5])
            k = get_ilm_key(i, l, m)
            if not k in q:
                # l + 1 for NULL at index 0
                q[k] = [0.0 for v in range(l + 1)]
            q[k][j] = q_of_i_j

    return t, q

def load_t_q_from_file(t_q_file):
    with open(t_q_file) as t_q_stream:
        t, q = load_t_q(t_q_stream)

    return t, q
            
def load_and_align(t_q_file, source_file, target_file, output_stream):
    t, q = load_t_q_from_file(t_q_file)
    align_files(t, q, source_file, target_file, output_stream)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print 'usage: %s t_q_file e_file, f_file' % sys.argv[0]
        sys.exit(1)

    load_and_align(sys.argv[1], sys.argv[3], sys.argv[2], sys.stdout)
