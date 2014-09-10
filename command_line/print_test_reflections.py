from __future__ import division

def print_refl(row):

  sbox = row['shoebox'].data
  mask = row['shoebox'].mask
  ndim = sbox.nd()
  dims = sbox.focus()

  from dials.algorithms.shoebox import MaskCode

  print '-' * 80

  print 'HKL:      %d %d %d' % row['miller_index']
  print 'S vector: %.3f %.3f %.3f' % row['s1']
  print 'Bounding: %d %d %d %d %d %d' % row['bbox']

  ''' FIX ME '''
  #print 'Frame:    %.3f' % refl.frame_number
  #print 'Position: %.3f %.3f' % refl.image_coord_px

  print '-' * 80

  for k in range(dims[0]):
    for j in range(dims[1]):
      for i in range(dims[2]):
        if mask[k, j, i] & MaskCode.BackgroundUsed and \
          mask[k, j, i] & MaskCode.Background:
          print '%4d#' % int(sbox[k, j, i]),
        elif mask[k, j, i] & MaskCode.BackgroundUsed:
          print '%4d*' % int(sbox[k, j, i]),
        elif mask[k, j, i] & MaskCode.Background:
          print '%4d-' % int(sbox[k, j, i]),
        else:
          print '%4d ' % int(sbox[k, j, i]),
      print
    print '-' * 80
  #'''

  return


if __name__ == '__main__':
  import cPickle as pickle
  import sys
  from dials.array_family import flex # import dependency
  table = pickle.load(open(sys.argv[1]))



  for i in range(len(table)):
    row = table[i]
    print '*' * 80
    print 'Reflection %d' % i
    print_refl(row)
    print '*' * 80

