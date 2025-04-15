import argparse
import os
from energy_meter import RpiEnergyMeter

def main():
    """
    Entry point for the RpiEnergyMeter application.

    This function parses command-line arguments and initializes the RpiEnergyMeter
    with the provided configuration and verbosity settings. It then runs the
    specified command with any additional arguments.

    Command-line arguments:
    - -c, --config <file>: Path to the config.toml file.
    - -v, --verbose: Enable verbose mode (optional, default is False).
    - command: Mode or module name to run.
    - arguments: Additional arguments for the selected mode/module.

    Returns:
    None
    """

    # First get generic paramters
    parser = argparse.ArgumentParser(prog="RpiEnergyMeter", add_help=True)
    parser.add_argument(
        "-c", "--config", metavar="<file>", help="Path to config.toml"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Verbose Mode",
        required=False,
        action="store_true",
        default=False,
    )

    parser.add_argument("command", help="Which mode to run")
    parser.add_argument(
        "arguments",
        nargs=argparse.REMAINDER,
        help="Additional arguments for the selected mode/module",
    )
    args = parser.parse_args()

    # then run the RpiEnergyMeter
    if args.config:
        os.environ["CONFIG"] = args.config

    if args.command == "tests":
        print("Running pylint")
        from pylint.lint import Run  # pylint: disable=import-outside-toplevel

        Run(["RpiEnergyMeter", "--exit-zero"], exit=False)

        # print("Running pytest")
        # import unittest
        # tests = unittest.TestLoader().discover('tests')
        # result = unittest.TextTestRunner(verbosity=2).run(tests)
    else:
        em = RpiEnergyMeter(args.config, args.verbose)
        em.main(args.command, args.Arguments)


if __name__ == "__main__":
    main()
