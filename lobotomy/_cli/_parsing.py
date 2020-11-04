import typing
import argparse


def parse(arguments: typing.List[str] = None) -> argparse.Namespace:
    """Parses command line arguments for command execution."""
    parser = argparse.ArgumentParser(
        prog="lobotomy",
        description="""
            Command line interface for lobotomy configuration
            management.
            """,
    )
    subparsers = parser.add_subparsers(title="command", dest="command")

    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("boto_operation")
    add_parser.add_argument("configuration_file_path")
    add_parser.add_argument(
        "--format",
        "--file-format",
        dest="file_format",
        choices=["yaml", "toml", "json"],
    )
    add_parser.add_argument("--prefix")

    return parser.parse_args(args=arguments)
