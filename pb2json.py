from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.internal.containers import BaseContainer, RepeatedCompositeFieldContainer, RepeatedScalarFieldContainer
from google.protobuf.internal.type_checkers import GetTypeChecker, TypeChecker
from google.protobuf.message import Message
import json
import re


def pb2json(pb):
    if isinstance(pb, BaseContainer):
        pb_list = []
        if isinstance(pb, RepeatedCompositeFieldContainer):
            for i in pb:
                pb_list.append(pb2json(i))
        else:
            for i in pb:
                if isinstance(i, basestring):
                    pb_list.append('"%s"' % i)
                if isinstance(i, bool):
                    pb_list.append('true' if i else 'false')
        return '[%s]' % ','.join(pb_list)
    s = ''
    for field, value in pb.ListFields():
        s = '{} "{}": %s,'.format(s, field.name)
        if field.type == FieldDescriptor.TYPE_MESSAGE or isinstance(value, BaseContainer):
            s = s % pb2json(value)
        elif field.type == FieldDescriptor.TYPE_STRING:
            s = s % ('"%s"' % value)
        elif field.type == FieldDescriptor.TYPE_BOOL:
            s = s % ('true' if field.value else 'false')
        else:
            s = s % value
    return '{%s}' % s.strip(', ')


def pb2dict(pb):
    # Deal with BaseContainer
    if isinstance(pb, RepeatedCompositeFieldContainer):
        return [pb2dict(i) for i in pb]
    elif isinstance(pb, RepeatedScalarFieldContainer):
        return [i for i in pb]
    pb_dict = {}
    for field, value in pb.ListFields():
        if field.type == FieldDescriptor.TYPE_MESSAGE:
            pb_dict[field.name] = pb2dict(value)
        else:
            pb_dict[field.name] = value
    return pb_dict


def dict2pb(D, pb):
    if isinstance(D, dict) is False:
        raise Exception
        # or `return`
    for k in D.iterkeys():
        if hasattr(pb, k):
            v = D.get(k)
            fd = getattr(pb, k)
            # BaseContainer: repeated
            if isinstance(fd, BaseContainer):
                if isinstance(v, (list, tuple)) is False:
                    raise Exception
                    # or `continue`
                # repeated message type
                if isinstance(fd, RepeatedCompositeFieldContainer):
                    for i in v:
                        dict2pb(v, fd.add())
                else:  # RepeatedScalarFieldContainer
                    # repeated basic type
                    fd = fd.extend(v)
            else:
                # non-repeated field, maybe message type
                if isinstance(fd, Message):
                    dict2pb(v, fd)
                else:
                    # Basic Type
                    setattr(pb, k, v)

    #reg = re.compile('["]{1}([^"]+)["]{1}\s*:\s*{')
