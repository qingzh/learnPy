import random
import string


def gen_random_chinese():
    '''
    @return a unicode: A Chinese

    GBK: 0x8140~0xfefe
    s = '%x%x' % (random.randint(0x81, 0xFE), random.randint(0x40, 0xFE))

    GB2312
    '''
    s = '%x%x' % (random.randint(0xB0, 0xF7), random.randint(0xA1, 0xFE))
    try:
        return s.decode('hex').decode('gbk')
    except UnicodeDecodeError:
        return gen_random_chinese()


def gen_random_ascii(length, unicode_encoded=True):
    '''
    @return unicode if `unicode_encoded == True` else string
    '''
    if length < 1:
        return ''
    s = ''.join(random.sample(string.ascii_letters + string.digits, length))
    if unicode_encoded:
        s = s.decode('utf8')
    return s
