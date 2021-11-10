from abc import ABC, abstractmethod

from jinja2 import ChoiceLoader, Environment, PackageLoader

from scitbx.array_family import flex


def generate_html_report(plots_data, filename):
    loader = ChoiceLoader(
        [
            PackageLoader("dials", "templates"),
            PackageLoader("dials", "static", encoding="utf-8"),
        ]
    )
    env = Environment(loader=loader)
    template = env.get_template("simple_report.html")
    html = template.render(
        page_title="DIALS SSX integration report",
        panel_title="Integration plots",
        graphs=plots_data,
    )
    with open(filename, "wb") as f:
        f.write(html.encode("utf-8", "xmlcharrefreplace"))


class SimpleIntegrator(ABC):

    """Define an interface for ssx prediction/integration processing"""

    def __init__(self, params):
        self.params = params

    @abstractmethod
    def run(self, experiment, table):
        # all gathering/collecting of output data should be optionally done at
        # the run level, so that the calls to individual processing steps are as
        # fast as possible.
        # In general, most output/statistics are calculable on the experiment
        # or reflection table.
        # However the refine step could be expected to return a json with
        # relevant history
        pass

    @abstractmethod
    def preprocess(experiment, reflection_table, *args, **kwargs):
        pass

    @abstractmethod
    def refine(experiment, reflection_table, *args, **kwargs):
        pass

    @abstractmethod
    def predict(experiment, reflection_table, *args, **kwargs):
        pass

    @abstractmethod
    def integrate(experiment, reflection_table, *args, **kwargs):
        pass


class NullCollector(object):

    """
    Defines a null data collector for cases where you don't want
    to record data during the process.
    """

    def __init__(self):
        self.data = {}

    def initial_collect(self, *args, **kwargs):
        pass

    def collect_after_preprocess(self, *args, **kwargs):
        pass

    def collect_after_refinement(self, *args, **kwargs):
        pass

    def collect_after_prediction(self, *args, **kwargs):
        pass

    def collect_after_integration(self, *args, **kwargs):
        pass


class OutputCollector(object):

    """
    Defines a data collector to log common quantities for all algorithm choices
    for an individual image.
    """

    def __init__(self):
        self.data = {}

    # collects general output for reporting, independent of underlying models,
    # for integration of a single image.

    def initial_collect(self, experiment, reflection_table):
        self.data["initial_n_refl"] = reflection_table.size()

    def collect_after_preprocess(self, experiment, reflection_table):
        self.data["n_strong_after_preprocess"] = reflection_table.size()
        n_sum = reflection_table.get_flags(reflection_table.flags.integrated_sum).count(
            True
        )
        self.data["n_strong_sum_integrated"] = n_sum

    def collect_after_refinement(self, experiment, reflection_table, refiner_output):
        if "initial_rmsd" not in self.data:
            self.data["initial_rmsd"] = refiner_output[-1][0]["rmsd"][0]
        self.data["final_rmsd"] = refiner_output[-1][0]["rmsd"][-1]

    def collect_after_prediction(self, experiment, reflection_table):
        pass

    def collect_after_integration(self, experiment, reflection_table):
        sel = reflection_table.get_flags(reflection_table.flags.integrated_sum)
        n_sum = sel.count(True)
        self.data["n_integrated"] = n_sum
        self.data["n_failed"] = reflection_table.size() - n_sum
        I = reflection_table["intensity.sum.value"].select(sel)
        var = reflection_table["intensity.sum.variance"].select(sel)
        if not var.all_gt(0):
            sel2 = var > 0
            I = I.select(sel2)
            var = var.select(sel2)
        self.data["i_over_sigma_overall"] = flex.mean(I / flex.sqrt(var))


class OutputAggregator:

    """
    Simple aggregator class to aggregate data from all images and generate
    json data for output/plotting.
    """

    def __init__(self):
        self.data = {}

    def add_dataset(self, collector, index):
        if collector.data:
            self.data[index] = collector.data

    def make_plots(self):
        # just make some simple plots for now as a test
        if not self.data:
            return {}
        I_over_sigma = [d["i_over_sigma_overall"] for d in self.data.values()]
        n = list(self.data.keys())
        n_integrated = [d["n_integrated"] for d in self.data.values()]
        initial_rmsds = [d["initial_rmsd"] for d in self.data.values()]
        final_rmsds = [d["final_rmsd"] for d in self.data.values()]

        plots_dict = {
            "I_over_sigma_overall": {
                "data": [
                    (
                        {
                            "x": n,
                            "y": I_over_sigma,
                            "type": "scatter",
                            "mode": "markers",
                        }
                    )
                ],
                "layout": {
                    "title": "Overall I/sigma per image",
                    "xaxis": {"title": "image number"},
                    "yaxis": {"title": "I/sigma"},
                },
            },
            "n_integrated": {
                "data": [
                    (
                        {
                            "x": n,
                            "y": n_integrated,
                            "type": "scatter",
                            "mode": "markers",
                        }
                    )
                ],
                "layout": {
                    "title": "Number of integrated reflections per image",
                    "xaxis": {"title": "image number"},
                    "yaxis": {"title": "N. reflections"},
                },
            },
            "rmsds": {
                "data": [
                    {
                        "x": n,
                        "y": initial_rmsds,
                        "type": "scatter",
                        "mode": "markers",
                        "name": "Initial rmsds",
                    },
                    {
                        "x": n,
                        "y": final_rmsds,
                        "type": "scatter",
                        "mode": "markers",
                        "name": "Final rmsds",
                    },
                ],
                "layout": {
                    "title": "Rmsds of integrated reflections per image",
                    "xaxis": {"title": "image number"},
                    "yaxis": {"title": "N. reflections"},
                },
            },
        }
        return plots_dict
