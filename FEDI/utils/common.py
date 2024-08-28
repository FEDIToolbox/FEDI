import argparse
from enum import Enum

class FEDI_ArgumentParser(argparse.RawTextHelpFormatter):
    """
    FEDI_ArgumentParser Class

    This class extends the functionality of Python's argparse.ArgumentParser to provide a
    more user-friendly and visually appealing command-line interface for the Fetal and 
    Neonatal Development Imaging (FEDI) Toolbox.

    """

    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = '\n\033[1mUSAGE\033[0m: \n\n    '
        return super(FEDI_ArgumentParser, self).add_usage(usage, actions, groups, prefix)

    def start_section(self, heading):
        if heading == 'description':
            heading = '\n\033[1mDESCRIPTION\033[0m \n\n    '
        if heading.lower() == 'options':
            heading = '\033[1mMANDATORY OPTIONS\033[0m' if heading == 'MANDATORY OPTIONS' else '\033[1mHELP\033[0m'
        super(FEDI_ArgumentParser, self).start_section(heading)

    def _format_action_invocation(self, action):
        if action.option_strings:
            invocation = ', '.join(action.option_strings)
            if action.nargs != 0:
                invocation += ' ' + self._format_args(action, action.dest.upper())
            return invocation
        else:
            return super(FEDI_ArgumentParser, self)._format_action_invocation(action)

    def format_help(self):
        # Custom header addition
        header = '\n\033[1m     Fetal and Neonatal Development Imaging - FEDI Toolbox\033[0m\n\n\n'
        return header + super(FEDI_ArgumentParser, self).format_help()

class Metavar(str, Enum):
    """
    Metavar Enum Class

    This class provides  labels for input types using the metavar field in argparse.

    Example usage in argparse:
        parser.add_argument('--input', metavar=Metavar.file.value, help='Input file')
    """
    file = "<file>"
    folder = "<folder>"
    str = "<str>"
    int = "<int>"
    float = "<float>"
    list = "<list>"
    bool = "<bool>"
    choice = "<choice>"
    path = "<path>"

    def __str__(self):
        return self.value
