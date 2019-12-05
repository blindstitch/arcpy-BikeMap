# Simplify usage of pprint. One object can be passed to pprint at a time
import pprint as ppp
pp=ppp.PrettyPrinter()
pprint=lambda p:pp.pprint(p)


# Write API requests as a dict before passing them
# TODO deprecate, using data={} in a request obj works better
def flatten_dict_for_api_request(dict): # This method rearranges the dict, since I am not using OrderedDicts... the API doesn't seem to care
    out = ''
    keys = dict.keys()
    for i in range(len(keys)):
        out += keys[i]
        out += '='
        out += dict[keys[i]]
        if i+1 != len(keys):
            out += '&'
    return out

# Split up the list into chunks that are bookended
# Ex: [1,2,3,4,5,6,7] => [[1,2,3],[3,4,5],[5,6,7]]
# Deprecated
def adjacent_chunks(list,chunk_size):
    if chunk_size > 1:
        list_out = []
        for i in range(0,len(list)-1,chunk_size-1):
            list_out.append(list[i:i+chunk_size])
        return list_out
    else:
        raise ValueError('Chunk size must be 2 or greater.')

# Break list into pieces of length chunk_size
def chunk(list, chunk_size):
    list_out = []
    if chunk_size > 1:
        for i in range(0,len(list)-1,chunk_size):
            list_out.append(list[i:i+chunk_size])
        return list_out
    else:
        raise ValueError('Chunk size must be 2 or greater.')

# Split list into 'adjacent' chunks that have an endpoint closest to a breakpoint
# Not really used either, 'midpoint' method used
# TODO adapted from methods found here https://arcpy.wordpress.com/2014/10/30/split-into-equal-length-features/
def adjacent_chunks_at_distance(dists,chunk_length,mode='index'):
    # Inputs:
    #  - List of distances along a line
    #  - The length of a chunk
    # Outputs:
    #  - Chunks or chunk indexes (use mode 'index' or mode 'chunks')

    from math import floor
    num_chunks = int(floor(max(dists) / float(chunk_length))) + 1
    split_points = []

    for i in range(int(num_chunks)):
        closest = min(dists, key=lambda x:abs(x - (chunk_length * i)))
        closest_index = dists.index(closest)
        split_points.append(closest_index)

    chunks_indexes = []

    # Produces 'adjacent' chunks. Method uses index+1 as last value of chunk
    for i in range(len(split_points)):
        if i is 0:
            breakpoints = [0,split_points[1] + 1]
            chunks_indexes.append(breakpoints)
        elif i is not len(split_points)-1:
            breakpoints = [split_points[i],split_points[i + 1] + 1]
            chunks_indexes.append(breakpoints)
        else:
            breakpoints = [split_points[i],None]
            chunks_indexes.append(breakpoints)

    chunks = [dists[chunk[0]:chunk[1]] for chunk in chunks_indexes]

    if mode == 'index':
        return chunks_indexes
    elif mode == 'chunks':
        return chunks
    elif mode == 'index_and_length':
        indexes_and_lengths = []
        for i in range(num_chunks):
            index = chunks_indexes[i][0]
            length = len(chunks[i])
            indexes_and_lengths.append([index,length])
        return indexes_and_lengths
    else:
        raise ValueError('Unrecognized mode "{}"'.format(mode))

# # Test data
# dists = [0,11,14,15,16,18,22,25,27,31,41,44,45,46,48,49,50,51,52,53,55,58,61,65,70,73,77,80,82,85,88,90,91,92,93,97,100]
# chunk_length = 30 # Must be float
#
# print adjacent_chunks_at_distance(dists,chunk_length,mode='index')
# print adjacent_chunks_at_distance(dists,chunk_length,mode='chunks')
# print adjacent_chunks_at_distance(dists,chunk_length,mode='index_and_length')

def clean(str,sep='_'):
    # Only return alnum with a separator
    # Your unicode strings will get mangled
    from re import sub
    return sub(r'^[\alnum]',sep,str.lower())