import argparse

class StorePassedAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # Record which args were passed by the user
        if not hasattr(namespace, '_explicit_args'):
            namespace._explicit_args = set()
        namespace._explicit_args.add(self.dest)
        setattr(namespace, self.dest, values)

