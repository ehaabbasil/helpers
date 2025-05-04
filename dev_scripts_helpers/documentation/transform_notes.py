#!/usr/bin/env python

"""
Perform one of several transformations on a txt file, e.g.,

1) `toc`: create table of context from the current file, with 1 level
    > transform_notes.py -a toc -i % -l 1

2) `format`: format the current file with 3 levels
    :!transform_notes.py -a format -i % --max_lev 3
    > transform_notes.py -a format -i notes/ABC.txt --max_lev 3

    - In vim
    :!transform_notes.py -a format -i % --max_lev 3
    :%!transform_notes.py -a format -i - --max_lev 3

3) `increase`: increase level
    :!transform_notes.py -a increase -i %
    :%!transform_notes.py -a increase -i -

4) `md_list_to_latex`: convert a markdown list to a latex list
    :!transform_notes.py -a md_list_to_latex -i %
    :%!transform_notes.py -a md_list_to_latex -i -

- The input or output can be filename or stdin (represented by '-')
- If output file is not specified then we assume that the output file is the
  same as the input
"""

import argparse
import hashlib
import logging

import dev_scripts_helpers.documentation.lint_notes as dshdlino
import helpers.hdbg as hdbg
import helpers.hlatex as hlatex
import helpers.hmarkdown as hmarkdo
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-a", "--action", required=True)
    hparser.add_input_output_args(parser)
    parser.add_argument("-l", "--max_lev", default=5)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hparser.init_logger_for_input_output_transform(args)
    #
    cmd = args.action
    max_lev = int(args.max_lev)
    #
    in_file_name, out_file_name = hparser.parse_input_output_args(
        args, clear_screen=True
    )
    if cmd == "test":
        # Compute the hash of a string to test the flow.
        txt = hparser.read_file(in_file_name)
        txt = "\n".join(txt)
        txt = hashlib.sha256(txt.encode("utf-8")).hexdigest()
        hparser.write_file(txt, out_file_name)
    elif cmd == "toc":
        txt = hparser.read_file(in_file_name)
        max_level = 3
        header_list = hmarkdo.extract_headers_from_markdown(
            txt, max_level=max_level
        )
        mode = "list"
        txt_out = hmarkdo.header_list_to_markdown(header_list, mode)
        hparser.write_file(txt_out, out_file_name)
    elif cmd == "format":
        hmarkdo.format_headers(in_file_name, out_file_name, max_lev)
    elif cmd == "increase":
        hmarkdo.modify_header_level(in_file_name, out_file_name, mode="increase")
    elif cmd == "md_list_to_latex":
        txt = hparser.read_file(in_file_name)
        txt = "\n".join(txt)
        txt = hlatex.markdown_list_to_latex(txt)
        hparser.write_file(txt, out_file_name)
    elif cmd == "md_remove_formatting":
        txt = hparser.read_file(in_file_name)
        txt = "\n".join(txt)
        txt = hmarkdo.remove_formatting(txt)
        hparser.write_file(txt, out_file_name)
    elif cmd == "md_clean_up":
        txt = hparser.read_file(in_file_name)
        txt = "\n".join(txt)
        txt = hmarkdo.md_clean_up(txt)
        txt = dshdlino.prettier_on_str(txt)
        hparser.write_file(txt, out_file_name)
    elif cmd == "md_format":
        txt = hparser.read_file(in_file_name)
        txt = "\n".join(txt)
        txt = dshdlino.prettier_on_str(txt)
        hparser.write_file(txt, out_file_name)
    else:
        assert 0, f"Invalid cmd='{cmd}'"


if __name__ == "__main__":
    _main(_parse())
