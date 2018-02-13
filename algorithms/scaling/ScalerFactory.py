'''
Collection of factories for creating the scalers.
'''
import logging
import pkg_resources
from dials.algorithms.scaling.Scaler import MultiScaler, TargetScaler, MultiScalerBase
logger = logging.getLogger('dials')

class Factory(object):
  '''
  Factory for creating Scalers.
  '''
  @classmethod
  def create(cls, params, experiments, reflections):
    '''
    create the scaling model defined by the params.
    '''
    if len(reflections) == 1:
      scaler = SingleScalerFactory.create(params, experiments[0], reflections[0])
    else:
      is_scaled_list = cls.is_scaled(experiments)
      n_scaled = is_scaled_list.count(True)
      if (params.scaling_options.target is True and n_scaled < len(reflections)
          and n_scaled > 0): #if only some scaled and want to do targeted scaling
        scaler = TargetScalerFactory.create(params, experiments, reflections,
          is_scaled_list)
      elif len(reflections) > 1: #else just make one multiscaler for all refls
        scaler = MultiScalerFactory.create(params, experiments, reflections)
      else:
        assert 0, 'no reflection tables found to create the scaler'
    return scaler

  @classmethod
  def is_scaled(cls, experiments):
    '''inspect scaling model to see if it has already been scaled.'''
    is_already_scaled = []
    for experiment in experiments:
      if experiment.scaling_model.is_scaled:
        is_already_scaled.append(True)
      else:
        is_already_scaled.append(False)
    return is_already_scaled


class SingleScalerFactory(object):
  'Factory for creating a scaler for a single dataset'
  @classmethod
  def create(cls, params, experiment, reflection, scaled_id=0):
    '''create a single scaler with the relevant parameterisation'''
    for entry_point in pkg_resources.iter_entry_points('dxtbx.scaling_model_ext'):
      if entry_point.name == experiment.scaling_model.id_:
        #finds relevant extension in dials.extensions.scaling_model_ext
        scalerfactory = entry_point.load().scaler()
        return scalerfactory(params, experiment, reflection, scaled_id)
    assert 0, "Unable to find Scaler in dials.extensions.scaling_model_ext"""

class MultiScalerFactory(object):
  'Factory for creating a scaler for multiple datasets'
  @classmethod
  def create(cls, params, experiments, reflections):
    '''create a list of single scalers to pass to a MultiScaler. For scaled_id,
    we just need unique values, not necessarily the same as previously.'''
    single_scalers = []
    for i, (reflection, experiment) in enumerate(zip(reflections, experiments)):
      single_scalers.append(SingleScalerFactory.create(
        params, experiment, reflection, scaled_id=i))
    return MultiScaler(params, experiments, single_scalers)

  @classmethod
  def create_from_targetscaler(cls, targetscaler):
    '''method to pass scalers from TargetScaler to a MultiScaler'''
    single_scalers = targetscaler.single_scalers
    for scaler in targetscaler.unscaled_scalers:
      single_scalers.append(scaler)
    return MultiScaler(targetscaler.params, [targetscaler.experiments], single_scalers)

class TargetScalerFactory(object):
  'Factory for creating a targeted scaler for multiple datasets'
  @classmethod
  def create(cls, params, experiments, reflections, is_scaled_list):
    '''sort scaled and unscaled datasets to pass to TargetScaler'''
    scaled_experiments = []
    scaled_scalers = []
    unscaled_experiments = []
    unscaled_scalers = []
    for i, reflection in enumerate(reflections):
      if is_scaled_list[i] is True:
        scaled_experiments.append(experiments[i])
        scaled_scalers.append(SingleScalerFactory.create(params, experiments[i],
          reflection, scaled_id=i))
      else:
        unscaled_experiments.append(experiments[i])
        unscaled_scalers.append(SingleScalerFactory.create(params, experiments[i],
          reflection, scaled_id=i))
    return TargetScaler(params, scaled_experiments, scaled_scalers,
      unscaled_experiments, unscaled_scalers)
