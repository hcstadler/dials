#!/usr/bin/env python
#
# config.py
#
#  Copyright (C) 2013 Diamond Light Source
#
#  Author: James Parkhurst
#
#  This code is distributed under the BSD license, a copy of which is
#  included in the root directory of this package.
from __future__ import division


class SystemConfigReader(object):
  '''Class to read system configuration.'''

  def __init__(self):
    '''Initialise the class.'''
    pass

  def master(self):
    '''Get the master config text.'''
    return '\n'.join([self._read_file(filename, True)
        for filename in self.master_filenames()])

  def user(self):
    '''Get the user config text.'''
    return self._read_file(self.user_filename(), False)

  def _read_file(self, filename, fail=False):
    '''Read the config file.'''

    # Try to read the phil file
    text = ''
    if filename:
      try:
        with open(filename, 'r') as f:
          text = f.read()
      except IOError:
        if fail:
          raise RuntimeError('error reading {0}'.format(filename))

    # Return the text
    return text

  def master_filenames(self):
    '''Get the master filename.'''
    import libtbx.load_env
    import os

    # Find the dials distribution directory
    path = libtbx.env.dist_path('dials')

    # Get the location of the master file
    return [os.path.join(path, 'data', 'logging.phil'),
            os.path.join(path, 'data', 'lookup.phil'),
            os.path.join(path, 'data', 'spotfinding.phil'),
            os.path.join(path, 'data', 'integration.phil'),
            os.path.join(path, 'data', 'refinement.phil')]

  def user_filename(self):
    '''Get the user filename.'''
    import os

    # Get the location of the user filename
    return os.path.join(os.path.expanduser('~'), '.dialsrc')


class SystemConfig(object):
  '''A class to read the system configuration.'''

  def __init__(self):
    '''Initialise the class.'''

    # Create the config file reader
    self._files = SystemConfigReader()

  def parse(self):
    '''Get the configuration.'''
    from iotbx.phil import parse

    # Read the master and user files
    master_text = self._files.master()
    user_text   = self._files.user()

    # Parse the files with phil
    self.master_phil  = parse(master_text)
    self.user_phil = parse(user_text)

    # Fetch the working phil from all the system sources
    return self.master_phil.fetch(sources = [self.user_phil])


class Config(object):
  ''' Manage configuration. '''

  def __init__(self):
    ''' Initialise by reading the system phil. '''
    self._system_config = SystemConfig()
    self._system_phil = self._system_config.parse()
    self._phil = self._system_phil
    self._params = self._phil.extract()

  def system_phil(self):
    ''' Return the system phil. '''
    return self._system_phil

  def phil(self):
    ''' Return the user phil. '''
    return self._phil

  def params(self):
    ''' Return the cached parameters. '''
    return self._params

  def parse(self, text):
    ''' Parse the given phil string. '''
    from iotbx.phil import parse
    phil = parse(text)
    self._phil = self._system_phil.fetch(sources=[phil])
    self._params = self._phil.extract()
