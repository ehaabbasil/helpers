"""
Import as:

import dev_scripts_helpers.thin_client.thin_client_utils as dshtctcut
"""

import argparse
import logging
import os
import sys

# We need to tweak `PYTHONPATH` directly since we are bootstrapping the system.
# sys.path.append("helpers_root")
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# Unfortunatelly, we need to hardcode this because
# of the inconsistent naming of the repos.
_REPO_DIR_MAPPING = {
    "amp": "cmamp",
    "helpers_root": "helpers",
}


# #############################################################################
# General
# #############################################################################


def get_git_root_dir() -> str:
    _, git_root_dir = hsystem.system_to_string("git rev-parse --show-toplevel")
    return git_root_dir


def get_home_dir() -> str:
    home_dir = os.environ["HOME"]
    return home_dir


def get_thin_environment_dir(dir_suffix: str) -> str:
    git_root_dir = get_git_root_dir()
    thin_environ_dir = f"{git_root_dir}/dev_scripts_{dir_suffix}/thin_client"
    return thin_environ_dir


def get_venv_dir(dir_suffix: str) -> str:
    home_dir = get_home_dir()
    venv_dir = f"{home_dir}/src/venv/client_venv.{dir_suffix}"
    return venv_dir


def get_tmux_session() -> str:
    rc, tmux_session = hsystem.system_to_string(
        "tmux display-message -p '#S'", abort_on_error=False
    )
    if rc != 0:
        tmux_session = ""
    return tmux_session


def inside_tmux() -> bool:
    return "TMUX" in os.environ


def dassert_not_inside_tmux():
    hdbg.dassert(not inside_tmux())


def system(cmd: str) -> None:
    print(hprint.frame(cmd))
    hsystem.system(cmd, suppress_output=False)


# #############################################################################
# Tmux
# #############################################################################


def create_parser(docstring: str) -> argparse.ArgumentParser:
    # Create the parser.
    parser = argparse.ArgumentParser(
        description=docstring,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_verbosity_arg(parser)
    parser.add_argument(
        "--do_not_confirm",
        action="store_true",
        help="Do not ask for user confirmation",
        required=False,
    )
    parser.add_argument(
        "--index",
        type=int,
        help="Index of the client (e.g., 1, 2, 3)",
        required=False,
    )
    parser.add_argument(
        "--force_restart",
        action="store_true",
        help="Destroy the existing tmux session and start a new one",
        required=False,
    )
    parser.add_argument(
        "--create_global_link",
        action="store_true",
        help="Create the link go_*.sh to this script in the home dir and exit",
        required=False,
    )
    return parser


# /////////////////////////////////////////////////////////////////////////////


def _create_new_window(
    window: str, color: str, dir_name: str, tmux_cmd: str
) -> None:
    cmd = f"tmux new-window -n '{window}'"
    hsystem.system(cmd)
    cmd = f"tmux send-keys '{color}; cd {dir_name} && {tmux_cmd}' C-m C-m"
    hsystem.system(cmd)


def _create_repo_windows(
    git_dir: str, setenv_path: str, module_name: str, is_submodule: bool
) -> None:
    """
    Create windows for the given module.
    """
    windows = ["dbash", "regr", "jupyter"]
    tmux_cmd = f"source {setenv_path}"
    # We create the first named named window only for submodule, for root
    # one it's created upon session creation.
    if is_submodule:
        # Somewhat clean-up the naming inconsistencies.
        module_window_name = module_name.rstrip("_root").upper()
        first_window = f"---{module_window_name}---"
        windows = [first_window] + windows
    # Create windows.
    for window in windows:
        _create_new_window(window, "green", git_dir, tmux_cmd)


def _go_to_first_window(tmux_name: str) -> None:
    hsystem.system(f"tmux select-window -t {tmux_name}:0")
    hsystem.system(f"tmux -2 attach-session -t {tmux_name}")


# /////////////////////////////////////////////////////////////////////////////


def _find_submodules(git_root_dir: str) -> list:
    """
    Find the names of all submodules in the given Git repository.

    :param git_root_dir: The root directory of the Git repository.
    :return: A list of names of all submodules found in the .gitmodules
        file. Returns an empty list if no submodules are found.
    """
    submodule_file = os.path.join(git_root_dir, ".gitmodules")
    submodules = []
    if os.path.exists(submodule_file):
        with open(submodule_file, "r") as file:
            for line in file:
                if line.strip().startswith("[submodule"):
                    submodule_name = line.split('"')[1]
                    submodules.append(submodule_name)
    return submodules


def _create_repo_tmux(
    git_root_dir: str, setenv_path: str, tmux_name: str
) -> None:
    """
    Create a new tmux session for the given Git repository.

    The function create window for the root AKA super module. After that
    it recursively searches for submodules and creates windows for each
    one. Currently only supports one submodule per repository.
    """
    # Create the sesson and first window.
    cmd = f"tmux new-session -d -s {tmux_name} -n '---{tmux_name}---'"
    hsystem.system(cmd)
    cmd = f"source {setenv_path}"
    cmd = f"tmux send-keys 'white; cd {git_root_dir} && {cmd}' C-m C-m"
    hsystem.system(cmd)
    # Handle all submodules.
    create_windows = True
    curr_git_dir = git_root_dir
    curr_setenv_path = setenv_path
    curr_module = tmux_name
    is_submodule = False
    while create_windows:
        _create_repo_windows(
            curr_git_dir, curr_setenv_path, curr_module, is_submodule
        )
        # After the initial, all other windows are created for a submodule.
        is_submodule = True
        submodules = _find_submodules(curr_git_dir)
        if len(submodules) >= 1:
            if len(submodules) > 1:
                _LOG.warning("Multiple submodules found: %s", submodules)
                _LOG.warning("Selecting only the first one: %s", submodules[0])
            curr_git_dir = os.path.join(curr_git_dir, submodules[0])
            curr_module = submodules[0]
            # Needed to map "amp" -> "dev_scripts_cmamp"
            # and helpers_root -> "dev_scripts_helpers"
            dev_scripts_suffix = _REPO_DIR_MAPPING.get(
                submodules[0], submodules[0]
            )
            dev_scripts_dir = f"dev_scripts_{dev_scripts_suffix}"
            curr_setenv_path = os.path.join(
                curr_git_dir, dev_scripts_dir, "thin_client/setenv.sh"
            )
            hdbg.dassert_file_exists(curr_setenv_path)
        else:
            _LOG.warning("No submodules found, ending the window creation")
            create_windows = False

    _go_to_first_window(tmux_name)


# /////////////////////////////////////////////////////////////////////////////


def create_tmux_session(
    parser: argparse.ArgumentParser,
    script_path: str,
    dir_suffix: str,
    setenv_path: str,
) -> None:
    """
    Creates a new tmux session or attaches to an existing one.

    This function checks if a tmux session with the given name (derived from
    `dir_suffix` and `index` argument) already exists. If it does, the function
    either attaches to the existing session or destroys it and creates a new
    one, based on the `force_restart` argument. If the session does not exist, a
    new one is created.

    The tmux session is configured based on the shell script specified by
    `setenv_path`.

    :param parser: Argument parser object.
    :param script_path: Path to the script file.
    :param dir_suffix: Prefix for the directory and tmux session name.
    :param setenv_path: Path to the shell script for setting up the environment.
    """
    print(f"##> {script_path}")
    # Parse the args.
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    #
    if args.create_global_link:
        _LOG.info("Creating the global link")
        hdbg.dassert_file_exists(script_path)
        cmd = f"ln -sf {script_path} ~/go_{dir_suffix}.py"
        system(cmd)
        _LOG.info("Link created: exiting")
        sys.exit(0)
    #
    hdbg.dassert_is_not(args.index, None, "Need to specify --index")
    idx = int(args.index)
    tmux_name = f"{dir_suffix}{idx}"
    _LOG.info("tmux_name=%s", tmux_name)
    #
    _LOG.debug("Checking if the tmux session '%s' already exists", tmux_name)
    _, tmux_session_str = hsystem.system_to_string(
        "tmux list-sessions", abort_on_error=False
    )
    _LOG.debug("tmux_session_str=\n%s", tmux_session_str)
    # E.g.,
    # ```
    # cmamp1: 4 windows (created Sun Aug  4 09:54:53 2024) (attached)
    # ...
    # ```
    tmux_sessions = [l.split(":")[0] for l in tmux_session_str.splitlines()]
    tmux_exists = tmux_name in tmux_sessions
    _LOG.debug("tmux_exists=%s", tmux_exists)
    if tmux_exists:
        # The tmux session exists.
        if args.force_restart:
            # Destroy the tmux session.
            _LOG.warning("The tmux session already exists: destroying it ...")
            current_tmux = get_tmux_session()
            system(f"tmux kill-session -t {current_tmux}")
        else:
            _LOG.info("The tmux session already exists: attaching it ...")
            # Make sure we are outside a tmux session.
            dassert_not_inside_tmux()
            # Attach the existing tmux session.
            system(f"tmux attach-session -t {tmux_name}")
            sys.exit(0)
    _LOG.info("The tmux session doesn't exist, creating it")
    # Make sure we are outside a tmux session.
    dassert_not_inside_tmux()
    if hserver.is_external_dev():
        _LOG.info("Inferred external setup")
        home_dir = get_home_dir()
    elif hserver.is_dev_csfy():
        _LOG.info("Inferred server setup")
        server_name = hsystem.get_server_name()
        hdbg.dassert_in(server_name, ["dev1", "dev2", "dev3"])
        user_name = hsystem.get_user_name()
        home_dir = f"/data/{user_name}"
    hdbg.dassert_ne(home_dir, "")
    _LOG.info("home_dir=%s", home_dir)
    # For encrypted dirs, such as `src_vc`, we use env vars to get path to keep things
    # compatible with the existing flow in `lemonade`.
    src_vc_dir = os.environ.get("AM_SRC_DIR", None)
    # Use encrypted dir path if specified, otherwise use the conventional `src`.
    src_dir = (
        src_vc_dir if src_vc_dir is not None else os.path.join(home_dir, "src")
    )
    git_root_dir = os.path.join(src_dir, tmux_name)
    _LOG.info("git_root_dir=%s", git_root_dir)
    # Create the tmux session.
    setenv_path = os.path.join(git_root_dir, setenv_path)
    _LOG.info("Checking if setenv_path=%s exists", setenv_path)
    hdbg.dassert_file_exists(setenv_path)
    _create_repo_tmux(git_root_dir, setenv_path, tmux_name)
