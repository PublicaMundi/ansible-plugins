#!/usr/bin/env python

import operator
import json

scalar_types = (basestring, int, float, complex, bool)
list_types = (list, set, tuple)
dict_types = (dict,)

unary_ops = {
   'not': operator.not_,
   'truth': operator.truth,
   'is': operator.is_,
   'is_not': operator.is_not,
}

binary_ops = {
   'eq': operator.eq,
   'le': operator.le,
   'ge': operator.ge,
   'lt': operator.lt,
   'gt': operator.gt,
   'ne': operator.ne,
}

def _flatten_list(pres, y):
    if not isinstance(y, list_types):
        pres.append(y)
    else:
        for yy in y:
            pres = _flatten_list(pres, yy)
    return pres

class FilterModule(object):
    '''Provide Jinja2 filters for Ansible
    
    The filters below are simplified wrappers on dict/list comprehension operations. 
    '''

    @staticmethod
    def one(l):
        n = len(l)
        if n > 1:
            raise ValueError('The list contains more than 1 element')
        elif n == 0:
            raise ValueError('The list is empty')
        else:
            return l[0]
    
    @staticmethod
    def to_map(l, item_key, path_delimiter='.'):
        '''Convert a list l into a dict using a given key from each item.
        The item_key may be a key path sepapated by path_delimiter.
        '''
        res = {}
        f = lambda z,k: z.get(k) if z else None
        p = item_key.split(path_delimiter)
        for x in l:
            k = reduce(f, p, x)
            if k:
                res[k] = x
        return res

    @staticmethod
    def format_items(it, fmt):
        '''Format items according to a format string `fmt`'''
        return [fmt.format(x) for x in it]

    @staticmethod
    def flatten_list(l):
        return reduce(_flatten_list, l, [])
    
    @staticmethod
    def list_values(d):
        '''List values from a dict'''
        return d.values()
    
    @staticmethod
    def list_keys(d):
        '''List keys from a dict'''
        return d.keys()
    
    @staticmethod
    def to_kv_pairs(d, sep=','):
        '''Format a dict as KV pairs'''
        f = lambda k, v: '{0}={1}'.format(k, v) if v else str(k)
        return sep.join([f(k, v)
            for k, v in d.items() if (not v or isinstance(v, scalar_types))])

    @staticmethod
    def map_keys(d, keys, source_path=None, path_delimiter='.', decode_json=False):
        '''Map keys on values from a set of (possibly nested) keys in an existing dict.
        
        If `keys` is the special value "*", then all keys from d are used. In any other
        case, an iterable of keys is expected.

        If `source_path` is supplied, then it is expected to be a format string and 
        contain placeholder for the current key item, e.g.:
        
        >>>  map_keys(d, ['aa', 'bb']) # visit actual and explicitly-defined keys
        >>>  map_keys(d, ['aa', 'bb'], 'someprefix-{0}')   # visit actual keys 
        >>>  map_keys(d, ['aa', 'bb'], 'prefix-{0}-suffix.version')  # visit nested keys
        
        '''

        # Find set of keys
        if keys == '*':
            keys = d.keys()
        else:
            assert isinstance(keys, (list, set)), 'Expected an iterable of keys'
        
        # Map keys to values
        res = None
        if isinstance(source_path, str):
            f = lambda z,k: z.get(k) if z else None
            res = {k: reduce(f, source_path.format(k).split(path_delimiter), d) 
                for k in keys}
        else:
            res = {k: d.get(k) for k in keys}
        
        # Done; decode values as JSON if requested
        if decode_json:
            return {k: json.loads(v) for k, v in res.iteritems()}
        else:
            return res

    @staticmethod
    def filter_by_key(l, key, op='exists', value=None):
        pred = None
        if op == 'exists':
            pred = lambda x: key in x
        elif op in unary_ops:
            t = unary_ops[op]
            pred = lambda x: (key in x) and t(x.get(key))
        elif op in binary_ops:
            t = binary_ops[op]
            pred = lambda x: (key in x) and t(x.get(key), value)
        if not pred:
            raise ValueError('Unknown operator: %s' %(op))
        return filter(pred, l)
    
    def filters(self):
        return {
           'one': self.one,
           'format_items': self.format_items,
           'flatten_list': self.flatten_list,
           'map_keys': self.map_keys,
           'list_values': self.list_values,
           'list_keys': self.list_keys,
           'to_kv_pairs': self.to_kv_pairs,
           'filter_by_key': self.filter_by_key,
           'to_map': self.to_map,
        }
