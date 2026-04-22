#!/usr/bin/env python3
"""
Boxes CLI => command line interface for boxes.py

Syntax:
boxes_cli [global parameters] command [command parameters]

Global parameters: 
    --verbose => enable verbose output
    --debug => enable debug output

The commands are:

    build [file_or_generator] [--parameters FILE] [generator_args] => create boxes from YAML config file or CLI arguments
    list [subcommand] => list generators, groups, lids, or edges
        list generators [patterns] => list all generators or those matching wildcards
        list groups [patterns] [--only-groups] => list groups and their generators
        list lids [patterns] => list lid styles and handle types
        list edges [patterns] => list edge types
    parameters [--dir directory] [--all] [--simple|--minimal] [generator ...] => creates YAML config files for every generator specified in the directory specified (default current dir), requires generator name(s) or --all flag. --simple outputs args only, --minimal outputs key-value pairs only
    box_yaml yaml_file => create a box from a yaml file
    merge => merge multiple boxes into one
    examples [--dir directory] => generate examples in examples folder (default examples/)

"""
from __future__ import annotations

import gettext
import os
import sys
import copy
import argparse
import logging
import hashlib
import fnmatch
from pathlib import Path
from typing import TextIO

try:
    import boxes
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
    import boxes

import boxes.generators
import boxes.svgmerge

import yaml

class ArgumentParserError(Exception): pass

class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)

def print_grouped_generators() -> None:
    class ConsoleColors:
        BOLD = '\033[1m'
        CLEAR = '\033[0m'
        ITALIC = '\033[3m'
        UNDERLINE = '\033[4m'

    print('Available generators:')
    for group in generator_groups():
        print('\n' + ConsoleColors.UNDERLINE + group.title + ConsoleColors.CLEAR)
        if group.description:
            print('\n' + group.description)
        print()
        for box in group.generators:
            description = box.__doc__ or ""
            description = description.replace("\n", "").replace("\r", "").strip()
            print(f' *  {box.__name__:<15} - {ConsoleColors.ITALIC}{description}{ConsoleColors.CLEAR}')

def multi_generate(config_path : Path|str|TextIO, output_path : Path|str, output_name_formater=None, format="svg") -> list[str]:
    if isinstance(config_path, str) or isinstance(config_path, Path):
        with open(config_path) as ff:
            config_data = yaml.safe_load(ff)
    else:
        config_data = yaml.safe_load(config_path)

    all_generators = boxes.generators.getAllBoxGenerators()
    generators_by_name = {b.__name__: b for b in all_generators.values()}

    generated_files = []
    defaults = config_data.get("Defaults", {})

    for ii, box_settings in enumerate(config_data.get("Boxes", [])):
        # Allow for skipping generation
        if box_settings.get("generate") == False:
            continue

        # Get the box generator
        box_type = box_settings.pop("box_type", None)
        if box_type is None:
            raise ValueError("box_type must be provided for each cut")

        # __ALL__ is a special case
        box_classes: tuple|None = None
        if box_type != "__ALL__":
            box_classes = ( generators_by_name.get(box_type, None), )
            if box_classes is None:
                raise ValueError("invalid generator '%s'" % box_type)
        else:
            skipGenerators = set(box_settings.get("skipGenerators", []))
            brokenGenerators = set(box_settings.get("brokenGenerators", []))
            avoidGenerators = skipGenerators | brokenGenerators
            box_classes = tuple(filter(lambda x: x.__name__ not in avoidGenerators, all_generators.values()))

        for box_cls in box_classes:
            box_cls_name = box_cls.__name__

            # Instantitate the box object
            box = box_cls()
            box.translations = get_translation()

            # Create the settings for the generator
            settings = copy.deepcopy(defaults)
            settings.update(box_settings.get("args", {}))

            # Handle layout separately
            if hasattr(box, "layout") and "layout" in settings:
                if os.path.exists(settings["layout"]):
                    with open(settings["layout"]) as ff:
                        settings["layout"] = ff.read()
                else:
                    box.layout = settings["layout"]

            # Turn the settings into arguments, but ignore format
            # in the YAML file if provided and use the argument to the function
            box_args = []
            for kk, vv in settings.items():
                # Handle format separately
                if kk in ("format","layout"):
                    continue
                box_args.append(f"--{kk}={vv}")

            # Layout has three options:
            #  - provided verbatim in the YAML file
            #  - provided as a path to a file in the YAML file
            #  - using the special placeholder __GENERATE__ which will invoke the default
            if "layout" in settings:
                if os.path.exists(settings["layout"]):
                    with open(settings["layout"]) as ff:
                        layout = ff.read()
                else:
                    layout = settings["layout"]
                box_args.append(f"--layout={layout}")

            # SVG is default, only apply argument if changing default
            if format != "svg":
                box_args.append(f"--format={format}")

            # Parse the box arguments - because we allow arguments at the
            # top-level defaults, we ignore unknown arguments
            try:
                # Ignore unknown arguments by pre-parsing. This two stage
                # approach was performed to avoid modifying parseArgs and
                # changing it's behavior.  A long-term better solution
                # might be to allow parseArgs to take a 'strict' argument
                # the can enable/disable strict parsing of arguments
                args, argv = box.argparser.parse_known_args(box_args)
                if len(argv) > 0:
                    for unknown_arg in argv:
                        box_args.remove(unknown_arg)
                box.parseArgs(box_args)
            except ArgumentParserError:
                logging.error("Error parsing box args for box %s : %s", ii, box_cls_name)
                continue

            # handle __GENERATE__ which must be called after parseArgs
            if getattr(box, "layout", None) == "__GENERATE__":
                if hasattr(box, "generate_layout") and callable(box.generate_layout):
                    box.layout = box.generate_layout()
                else:
                    logging.error("Error box %s : %s requires manual layout", ii, box_cls_name)
                    continue

            box.metadata["reproducible"] = True

            # Render the box SVG
            box.open()
            box.render()
            data = box.close()

            if callable(output_name_formater):
                output_fname = output_name_formater(
                    box_type=box_cls_name,
                    name=box_settings.get("name", box_cls_name),
                    box_idx=ii,
                    metadata=box.metadata,
                    box_args=box_args
                )
            else:
                output_fname = output_name_formater.format(
                    box_type=box_cls_name,
                    name=box_settings.get("name", box_cls_name),
                    box_idx=ii,
                    metadata=box.metadata,
                )

            # Write the output - if count is provided generate multiple copies
            if box_settings.get("count") is not None:
                for jj in range(int(box_settings.get("count"))):
                    output_file = os.path.join(output_path, f"{output_fname}_{jj}.{format}")
                    logging.info(f"Writing {output_file}")
                    with open(output_file, "wb") as ff:
                        ff.write(data.read())
                        data.seek(0)
                    generated_files.append(output_file)

            else:
                output_file = os.path.join(output_path, f"{output_fname}.{format}")
                logging.info(f"Writing {output_file}")
                with open(output_file, "wb") as ff:
                    ff.write(data.read())
                generated_files.append(output_file)

    return generated_files

def get_translation():
    try:
        return gettext.translation('boxes.py', localedir='locale')
    except OSError:
        return gettext.translation('boxes.py', fallback=True)


def run_generator(name: str, args) -> None:
    generators = generators_by_name()
    lower_name = name.lower()

    if lower_name in generators.keys():
        box = generators[lower_name]()
        box.translations = get_translation()
        box.parseArgs(args)
        box.open()
        box.render()
        data = box.close()
        with os.fdopen(sys.stdout.fileno(), "wb", closefd=False) if box.output == "-" else open(box.output, 'wb') as f:
            f.write(data.getvalue())
    else:
        msg = f"Unknown generator '{name}'. Use boxes --list to get a list of available commands.\n"
        sys.stderr.write(msg)


def generator_groups():
    generators = generators_by_name()
    return group_generators(generators)


def group_generators(generators):
    groups = boxes.generators.ui_groups
    groups_by_name = boxes.generators.ui_groups_by_name

    for name, generator in generators.items():
        group_for_generator = groups_by_name.get(generator.ui_group, groups_by_name['Misc'])
        group_for_generator.add(generator)

    return groups


def generators_by_name() -> dict[str, type[boxes.Boxes]]:
    all_generators = boxes.generators.getAllBoxGenerators()

    return {
        name.split('.')[-1].lower(): generator
        for name, generator in all_generators.items()
    }


def example_output_fname_formatter(box_type, name, box_idx, metadata, box_args):
    if not box_args:
        return f"{name}"
    else:
        args_hash = hashlib.sha1(" ".join(sorted(box_args)).encode("utf-8")).hexdigest()
        return f"{name}_{args_hash[0:8]}"


def _format_yaml_value(value) -> str:
    """Format a value for YAML output."""
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, list):
        return str(value)
    else:
        return f'"{str(value)}"'


def generate_yaml_for_generator(cls, output_dir: str, format_type: str = "full") -> str | None:
    """Generate a YAML file for a single generator.
    
    Args:
        cls: Generator class
        output_dir: Output directory for the file
        format_type: One of "full", "simple" (just args), or "minimal" (key-value pairs)
    """
    gname = cls.__name__

    try:
        b = cls()

        # Collect all parameters from argument groups
        args_dict = {}
        for grp in b.argparser._action_groups:
            # Skip the "optional arguments" group which contains --help etc
            if grp.title in ['optional arguments', 'options']:
                continue

            for a in grp._group_actions:
                if isinstance(a, argparse._HelpAction):
                    continue

                # Get parameter name (remove leading dashes)
                param_name = None
                for flag in getattr(a, 'option_strings', []):
                    if flag.startswith('--'):
                        param_name = flag[2:]
                        break
                    elif flag.startswith('-') and not flag.startswith('--'):
                        param_name = flag[1:]
                        break

                if param_name and param_name != 'help':
                    # Get default value
                    default_value = getattr(a, 'default', None)
                    args_dict[param_name] = default_value

        yaml_lines = []
        yaml_lines.append("# Generated YAML configuration for " + gname)
        
        if format_type == "simple":
            # Simple format: just args section
            yaml_lines.append("# Simple format (args only)")
            yaml_lines.append("")
            yaml_lines.append("args:")
            
            for param_name, default_value in sorted(args_dict.items()):
                value_str = _format_yaml_value(default_value)
                yaml_lines.append(f"  {param_name}: {value_str}")
                
        elif format_type == "minimal":
            # Minimal format: just key-value pairs
            yaml_lines.append("# Minimal format (key-value pairs)")
            yaml_lines.append("")
            
            for param_name, default_value in sorted(args_dict.items()):
                value_str = _format_yaml_value(default_value)
                yaml_lines.append(f"{param_name}: {value_str}")
                
        else:  # full format
            # Full format with Defaults and Boxes sections
            yaml_lines.append("# Full format with Defaults and Boxes sections")
            yaml_lines.append("# This file can be used with boxes_generator.py or the build command")
            yaml_lines.append("")
            yaml_lines.append("Defaults:")
            yaml_lines.append("    reference: 0")
            yaml_lines.append("")
            yaml_lines.append("Boxes:")
            yaml_lines.append("  - box_type: " + gname)
            yaml_lines.append("    name: \"" + gname + "_example\"")
            yaml_lines.append("    generate: true")
            yaml_lines.append("    args:")

            # Add parameters grouped by argument groups
            for group in b.argparser._action_groups[3:] + b.argparser._action_groups[:3]:
                if not group._group_actions:
                    continue
                if len(group._group_actions) == 1 and isinstance(group._group_actions[0], argparse._HelpAction):
                    continue
                if group.title in ['optional arguments', 'options']:
                    continue

                # Add group name as comment
                yaml_lines.append(f"      ## {group.title}")

                # Process arguments in this group
                group_args = []
                for a in group._group_actions:
                    if isinstance(a, argparse._HelpAction):
                        continue
                    if a.dest in ("input", "output"):
                        continue

                    # Get parameter name (remove leading dashes)
                    param_name = None
                    for flag in getattr(a, 'option_strings', []):
                        if flag.startswith('--'):
                            param_name = flag[2:]
                            break
                        elif flag.startswith('-') and not flag.startswith('--'):
                            param_name = flag[1:]
                            break

                    if param_name and param_name != 'help':
                        default_value = getattr(a, 'default', None)
                        help_text = getattr(a, 'help', '')
                        value_str = _format_yaml_value(default_value)
                        group_args.append((param_name, value_str, help_text))

                # Sort arguments within the group and add them
                for param_name, value_str, help_text in sorted(group_args):
                    if help_text:
                        yaml_lines.append(f"      # {help_text}")
                    yaml_lines.append(f"      {param_name}: {value_str}")

                # Add empty line after each group for readability
                if group_args:
                    yaml_lines.append("")

        # Write to file
        filename = os.path.join(output_dir, f"{gname.lower()}.yaml")
        with open(filename, 'w') as f:
            f.write('\n'.join(yaml_lines))

        return filename

    except Exception as e:
        logging.error(f"Error generating YAML for {gname}: {e}")
        return None


def cmd_parameters(args) -> None:
    """Handle parameters command"""
    base_output_dir = args.dir
    os.makedirs(base_output_dir, exist_ok=True)

    all_generators = boxes.generators.getAllBoxGenerators()

    if args.all:
        # Generate all generators with webinterface
        generators_to_dump = [
            cls for cls in all_generators.values()
            if getattr(cls, 'webinterface', False)
        ]
    else:
        # Generate only specified generators
        generators_to_dump = []
        for name in args.generators:
            found = False
            for full_name, cls in all_generators.items():
                if cls.__name__.lower() == name.lower():
                    generators_to_dump.append(cls)
                    found = True
                    break
            if not found:
                logging.warning(f"Warning: Generator '{name}' not found")

    generated_files = []
    errors = {}

    for cls in generators_to_dump:
        gname = cls.__name__
        try:
            # Determine output directory based on mode
            if args.all:
                # Get the UI group for this generator
                group_name = getattr(cls, 'ui_group', 'Misc')
                group_dir = os.path.join(base_output_dir, group_name)
                os.makedirs(group_dir, exist_ok=True)
                output_dir = group_dir
            else:
                output_dir = base_output_dir

            # Determine format type
            format_type = "full"
            if getattr(args, 'simple', False):
                format_type = "simple"
            elif getattr(args, 'minimal', False):
                format_type = "minimal"
                
            filename = generate_yaml_for_generator(cls, output_dir, format_type)
            if filename:
                generated_files.append(filename)
                logging.info(f"Created {format_type} config {filename}")
        except Exception as e:
            errors[gname] = repr(e)
            logging.error(f"Error with {gname}: {e}")

    if base_output_dir == ".":
        base_output_text = "current"
    else:
        base_output_text = f"'{base_output_dir}'"

    logging.info(f"Created {len(generated_files)} config files in {base_output_text} directory")
    if errors:
        logging.error(f"Errors encountered: {len(errors)}")
        for name, error in errors.items():
            logging.error(f"  {name}: {error}")


def cmd_box_yaml(args) -> None:
    """Handle box_yaml command"""
    yaml_file = args.yaml_file
    output_path = Path(args.output_dir) if args.output_dir else Path(".")
    output_fname_format = "{name}_{box_idx}"
    multi_generate(yaml_file, output_path, output_fname_format)


def cmd_examples(args) -> None:
    """Handle examples command"""
    if args.examples:
        config_files = [Path(__file__).parent.parent.parent / 'examples.yml']
        logging.info("Generating SVG examples from default config.")
    else:
        config_files = [Path(c) for c in args.config]
        for config_path in config_files:
            logging.info(f"Generating SVG examples from {config_path}.")
    output_path = Path(args.dir)
    output_path.mkdir(parents=True, exist_ok=True)
    for config_path in config_files:
        multi_generate(config_path, output_path, example_output_fname_formatter)


def cmd_merge(args) -> None:
    """Handle merge command"""
    merger = boxes.svgmerge.SvgMerge()
    merger.parseArgs(args.merge_args)
    merger.render(args.merge_args)
    data = merger.close()
    with os.fdopen(sys.stdout.fileno(), "wb", closefd=False) if merger.output == "-" else open(merger.output, 'wb') as f:
        f.write(data.getvalue())


def load_yaml_data(yaml_file: str) -> dict:
    """Load YAML file and return parsed data."""
    with open(yaml_file) as f:
        return yaml.safe_load(f)


def yaml_to_args(data: dict) -> list[tuple[str, any]]:
    """Convert YAML data to list of (key, value) tuples.
    
    Supports multiple formats:
    - Full format with Defaults and Boxes sections (yields each box)
    - Simple format with args at top level
    - Minimal format with key-value pairs
    """
    # Handle full format with Boxes section - yield each box as separate arg set
    if isinstance(data, dict) and "Boxes" in data and data["Boxes"]:
        for box_data in data["Boxes"]:
            box_type = box_data.get("box_type")
            args_list = []
            if box_type:
                args_list.append(("box_type", box_type))
            if "args" in box_data:
                for key, value in box_data["args"].items():
                    if value is not None:
                        args_list.append((key, value))
            # Also check for direct keys in box_data (like name, generate)
            for key in ["name", "generate"]:
                if key in box_data:
                    args_list.append((key, box_data[key]))
            yield args_list
    # Handle simple format with args directly at top level
    elif isinstance(data, dict) and "args" in data:
        yield [(key, value) for key, value in data["args"].items() if value is not None]
    # Handle minimal format with just key-value pairs
    elif isinstance(data, dict):
        yield [(key, value) for key, value in data.items() 
               if key not in ("Defaults", "Boxes") and value is not None]


def parse_arg_to_tuple(arg: str) -> tuple[str, any]:
    """Parse a command line argument to (key, value) tuple."""
    if arg.startswith('--'):
        arg = arg[2:]
    elif arg.startswith('-'):
        arg = arg[1:]
    
    if '=' in arg:
        key, value = arg.split('=', 1)
    else:
        key = arg
        value = True
    
    # Try to convert value to appropriate type
    if isinstance(value, str):
        # Try int
        try:
            value = int(value)
        except ValueError:
            # Try float
            try:
                value = float(value)
            except ValueError:
                # Try bool
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
    
    return key, value


def cmd_build(args) -> None:
    """Handle build command - generate boxes from YAML configuration file or CLI arguments.
    
    Accepts a Full format YAML file with Defaults and Boxes sections, or
    a generator name as positional argument to specify the generator directly.
    Each box is generated with accumulated parameters.
    Additional --parameters files and CLI arguments can be specified
    to override or add to the configuration.
    """
    import os
    from boxes.generators import getAllBoxGenerators
    
    # Determine if positional argument is a file or generator name
    main_config = {}
    cli_box_type = None
    
    if args.file_or_generator:
        file_or_gen = args.file_or_generator
        if os.path.isfile(file_or_gen):
            # It's a config file
            logging.info(f"Reading main configuration file: {file_or_gen}")
            main_config = load_yaml_data(file_or_gen)
            logging.info(f"Loaded configuration from {file_or_gen}")
        else:
            # Check if it's a valid generator name (just the class name)
            all_generators = getAllBoxGenerators()
            # Create mapping from simple class name to full generator name
            generator_map = {name.split('.')[-1].lower(): name for name in all_generators.keys()}
            if file_or_gen.lower() in generator_map:
                cli_box_type = file_or_gen
                logging.info(f"Using generator from positional argument: {file_or_gen}")
            else:
                # Get just the class names for error message
                simple_names = sorted(set(name.split('.')[-1] for name in all_generators.keys()))
                logging.error(f"Error: '{file_or_gen}' is not a file and not a valid generator name")
                logging.error(f"Valid generators: {', '.join(simple_names)}")
                return
    
    # Start with defaults if present
    defaults = main_config.get("Defaults", {}) if isinstance(main_config, dict) else {}
    if defaults:
        logging.info(f"Defaults: {defaults}")
    
    # Collect all argument sources in order:
    # 1. Defaults from main config
    # 2. Boxes from main config (each box triggers generation)
    # 3. --box_type from CLI (creates a single box config)
    # 4. Additional --parameters files
    # 5. CLI generator_args
    
    # Process boxes from main config
    boxes_list = []
    if isinstance(main_config, dict) and "Boxes" in main_config and main_config["Boxes"]:
        boxes_list = main_config["Boxes"]
        logging.info(f"Found {len(boxes_list)} box(es) in config file")
    
    # If box_type is provided via CLI, add it as a box (or override first box)
    if cli_box_type:
        if boxes_list:
            # Override the first box's box_type
            boxes_list[0]["box_type"] = cli_box_type
            logging.info(f"Overriding box_type with CLI argument: {cli_box_type}")
        else:
            # Create a new box entry
            boxes_list.append({"box_type": cli_box_type})
            logging.info(f"Creating single box from CLI: {cli_box_type}")
    
    # Check if we have any boxes to generate
    if not boxes_list:
        logging.error("Error: No box_type defined. Provide a config file with Boxes, or use --box_type")
        return
    
    # Additional parameters from --parameters files
    extra_params: list[tuple[str, any]] = []
    if args.parameters:
        for param_file in args.parameters:
            logging.info(f"Reading additional parameter file: {param_file}")
            data = load_yaml_data(param_file)
            for arg_list in yaml_to_args(data):
                extra_params.extend(arg_list)
        if args.verbose and extra_params:
            logging.info(f"Loaded {len(extra_params)} additional parameter(s) from --parameters files")
    
    # CLI arguments
    cli_params: list[tuple[str, any]] = []
    if args.generator_args:
        for arg in args.generator_args:
            cli_params.append(parse_arg_to_tuple(arg))
        if args.verbose and cli_params:
            logging.info(f"Loaded {len(cli_params)} parameter(s) from command line")
    
    # Generate each box
    box_idx = 0
    for box_data in boxes_list:
        box_idx += 1
        # Start with defaults
        current_params = dict(defaults)
        
        # Add box-specific settings
        if "box_type" in box_data:
            current_params["box_type"] = box_data["box_type"]
        if "args" in box_data:
            for key, value in box_data["args"].items():
                if value is not None:
                    current_params[key] = value
        # Copy other keys (name, generate, etc.)
        for key in ["name", "generate"]:
            if key in box_data:
                current_params[key] = box_data[key]
        
        box_type = current_params.get("box_type", "unknown")
        box_name = current_params.get("name", f"box_{box_idx}")
        
        logging.info(f"Processing box {box_idx}: {box_name} (type: {box_type})")
        
        # Apply extra params from --parameters files (overwrite)
        if extra_params:
            for key, value in extra_params:
                if key == "box_type":
                    current_params[key] = value
                else:
                    current_params[key] = value
            logging.info(f"Applied {len(extra_params)} parameter(s) from --parameters files")
        
        # Apply CLI params (overwrite)
        if cli_params:
            for key, value in cli_params:
                if key == "box_type":
                    current_params[key] = value
                else:
                    current_params[key] = value
            logging.info(f"Applied {len(cli_params)} parameter(s) from command line")
        
        # Check if box should be skipped
        if not current_params.get("box_type"):
            logging.info(f"Skipping box {box_idx}: no box_type specified")
            continue
        if current_params.get("generate", True) == False:
            logging.info(f"Skipping box {box_idx}: generate is set to false")
            continue
        
        # Generate the box
        logging.info(f"Creating box: {box_type} (name: {box_name})")
        _generate_box(current_params, args.verbose, args.debug)
        logging.info(f"Finished creating box: {box_name}")
    
    logging.info(f"Build complete. Generated {box_idx} box(es).")


def _generate_box(params: dict[str, any], verbose: bool, debug: bool) -> None:
    """Generate a single box with the given parameters."""
    box_type = params.pop("box_type")
    
    # Convert params to command line format
    extra = []
    for key, value in params.items():
        if value is not None:
            extra.append(f"--{key}={value}")
    
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    run_generator(box_type, extra)


def wildcard_match(pattern: str, text: str) -> bool:
    """Simple wildcard matching using fnmatch-style patterns."""
    return fnmatch.fnmatch(text.lower(), pattern.lower())


def cmd_list(args) -> None:
    """Handle list command with subcommands"""
    if args.list_command == "generators":
        cmd_list_generators(args)
    elif args.list_command == "groups":
        cmd_list_groups(args)
    elif args.list_command == "lids":
        cmd_list_lids(args)
    elif args.list_command == "edges":
        cmd_list_edges(args)
    else:
        # Default behavior: list generators grouped by category
        print_grouped_generators()


def cmd_list_generators(args) -> None:
    """Handle list generators subcommand"""
    all_generators = boxes.generators.getAllBoxGenerators()
    patterns = args.patterns if args.patterns else ["*"]

    class ConsoleColors:
        BOLD = '\033[1m'
        CLEAR = '\033[0m'
        ITALIC = '\033[3m'

    matched = []
    for full_name, generator in all_generators.items():
        name = generator.__name__
        for pattern in patterns:
            if wildcard_match(pattern, name):
                description = generator.__doc__ or ""
                description = description.replace("\n", "").replace("\r", "").strip()
                matched.append((name, description))
                break

    if matched:
        print(f"Available generators matching {patterns}:")
        print()
        for name, description in sorted(matched, key=lambda x: x[0]):
            print(f"  {name:<20} - {ConsoleColors.ITALIC}{description}{ConsoleColors.CLEAR}")
    else:
        print(f"No generators found matching patterns: {patterns}")


def cmd_list_groups(args) -> None:
    """Handle list groups subcommand"""
    patterns = args.patterns if args.patterns else ["*"]
    only_groups = args.only_groups

    class ConsoleColors:
        BOLD = '\033[1m'
        CLEAR = '\033[0m'
        ITALIC = '\033[3m'
        UNDERLINE = '\033[4m'

    groups = generator_groups()
    matched_groups = []

    for group in groups:
        for pattern in patterns:
            if wildcard_match(pattern, group.title):
                matched_groups.append(group)
                break

    if not matched_groups:
        print(f"No groups found matching patterns: {patterns}")
        return

    print("Groups:")
    for group in matched_groups:
        print('\n' + ConsoleColors.UNDERLINE + group.title + ConsoleColors.CLEAR)
        if group.description:
            print('\n' + group.description)
        if not only_groups:
            print()
            for generator in group.generators:
                description = generator.__doc__ or ""
                description = description.replace("\n", "").replace("\r", "").strip()
                print(f"  {generator.__name__:<15} - {ConsoleColors.ITALIC}{description}{ConsoleColors.CLEAR}")


def cmd_list_lids(args) -> None:
    """Handle list lids subcommand"""
    patterns = args.patterns if args.patterns else ["*"]

    from boxes.lids import LidSettings
    styles = LidSettings.absolute_params["style"]
    handles = LidSettings.absolute_params["handle"]
    style_descriptions = LidSettings.style_descriptions
    handle_descriptions = LidSettings.handle_descriptions

    class ConsoleColors:
        BOLD = '\033[1m'
        CLEAR = '\033[0m'
        ITALIC = '\033[3m'

    print("Lid styles:")
    print()
    matched_styles = [s for s in styles if any(wildcard_match(p, s) for p in patterns)]
    if matched_styles:
        for style in matched_styles:
            desc = style_descriptions.get(style, "")
            print(f"  {ConsoleColors.BOLD}{style}{ConsoleColors.CLEAR} - {ConsoleColors.ITALIC}{desc}{ConsoleColors.CLEAR}")
    else:
        print(f"  (no matches)")

    print("\nHandle types:")
    print()
    matched_handles = [h for h in handles if any(wildcard_match(p, h) for p in patterns)]
    if matched_handles:
        for handle in matched_handles:
            desc = handle_descriptions.get(handle, "")
            print(f"  {ConsoleColors.BOLD}{handle}{ConsoleColors.CLEAR} - {ConsoleColors.ITALIC}{desc}{ConsoleColors.CLEAR}")
    else:
        print(f"  (no matches)")


def cmd_list_edges(args) -> None:
    """Handle list edges subcommand"""
    patterns = args.patterns if args.patterns else ["*"]

    import inspect
    from boxes import edges as edges_module

    class ConsoleColors:
        BOLD = '\033[1m'
        CLEAR = '\033[0m'

    # Find all edge classes with a char attribute
    edge_classes = []
    for name, obj in inspect.getmembers(edges_module):
        if inspect.isclass(obj) and hasattr(obj, 'char') and hasattr(obj, 'description'):
            if obj.char:  # Only include edges with a defined char
                edge_classes.append((obj.char, obj.description))

    # Get additional aliases from getDescriptions
    descriptions = edges_module.getDescriptions()

    print("Edges:")
    print()
    matched = []
    for char, desc in edge_classes:
        # Match against char or description
        for pattern in patterns:
            if wildcard_match(pattern, char) or wildcard_match(pattern, desc):
                matched.append((char, desc))
                break

    if matched:
        for char, desc in sorted(matched, key=lambda x: x[0]):
            print(f"  {ConsoleColors.BOLD}{char}{ConsoleColors.CLEAR} - {desc}")
    else:
        print(f"  No edges found matching patterns: {patterns}")


def main(argv: list[str] | None = None) -> None:
    # Create main parser
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
        add_help=True
    )
    parser.allow_abbrev = False

    # Global parameters
    parser.add_argument("--verbose", action="store_true", default=False,
                        help="Enable verbose output")
    parser.add_argument("--debug", action="store_true", default=False,
                        help="Enable debug output")
    parser.add_argument("--id", type=str, default=None, help="ignored")

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # build command - create boxes from YAML config file
    build_parser = subparsers.add_parser("build",
        help="Create boxes from a YAML configuration file",
        description="Create one or more boxes from a YAML configuration file.\n\n"
                    "The YAML file should be in 'Full format' with 'Defaults' and 'Boxes' sections.\n"
                    "Each box in 'Boxes' will be generated. Additional --parameters files and CLI\n"
                    "arguments can override or add to the configuration.\n\n"
                    "YAML file format:\n"
                    "  Defaults:\n"
                    "    reference: 0\n"
                    "  Boxes:\n"
                    "    - box_type: ABox\n"
                    "      name: \"mybox\"\n"
                    "      args:\n"
                    "        thickness: 4.0\n"
                    "        output: mybox.svg\n\n"
                    "Examples:\n"
                    "  boxes_cli build ABox --thickness=5.0 --output=box.svg\n"
                    "  boxes_cli build config.yaml\n"
                    "  boxes_cli build config.yaml --parameters=overrides.yaml\n\n"
                    "Common CLI overrides:\n"
                    "  --output FILE         Name of the output file\n"
                    "  --format FORMAT       Output format (svg, pdf, ps, etc.)\n"
                    "  --thickness MM        Material thickness in mm\n"
                    "  --burn MM             Burn correction in mm\n"
                    "  --labels BOOL         Label the parts\n"
                    "  --parameters FILE     Additional YAML file(s) with parameters")
    build_parser.add_argument("file_or_generator", type=str, nargs="?", default=None,
                              help="YAML config file (if exists) or generator name (e.g., ABox, UniversalBox)")
    build_parser.add_argument("--parameters", type=str, nargs="*",
                              help="Additional YAML file(s) with parameters to use (can be specified multiple times)")
    build_parser.add_argument("generator_args", nargs=argparse.REMAINDER,
                            help="Generator parameters to override (e.g., --output=mybox.svg --thickness=4.0)")

    # list command with subcommands
    list_parser = subparsers.add_parser("list", help="List generators, groups, lids, or edges")
    list_subparsers = list_parser.add_subparsers(dest="list_command", help="List subcommands")

    # list generators - list all generators or specific ones
    list_gen_parser = list_subparsers.add_parser("generators", help="List generator names")
    list_gen_parser.add_argument("patterns", type=str, nargs="*", help="Generator name patterns (accepts wildcards)")

    # list groups - list all groups
    list_groups_parser = list_subparsers.add_parser("groups", help="List generator groups")
    list_groups_parser.add_argument("patterns", type=str, nargs="*", help="Group name patterns (accepts wildcards)")
    list_groups_parser.add_argument("--only-groups", action="store_true", default=False, help="List only groups, not their generators")

    # list lids - list all lid types
    list_lids_parser = list_subparsers.add_parser("lids", help="List lid styles and handle types")
    list_lids_parser.add_argument("patterns", type=str, nargs="*", help="Lid style/handle patterns (accepts wildcards)")

    # list edges - list all edge types
    list_edges_parser = list_subparsers.add_parser("edges", help="List edge types")
    list_edges_parser.add_argument("patterns", type=str, nargs="*", help="Edge character or description patterns (accepts wildcards)")

    # parameters command
    parameters_parser = subparsers.add_parser("parameters", help="Generate YAML configuration files for generators")
    parameters_parser.add_argument("--dir", type=str, default=".",
                                      help="Output directory for YAML files (default: current dir)")
    parameters_parser.add_argument("--all", action="store_true", default=False,
                                      help="Create config files for all generators")
    format_group = parameters_parser.add_mutually_exclusive_group()
    format_group.add_argument("--simple", action="store_true", default=False,
                              help="Output in simple format (args section only)")
    format_group.add_argument("--minimal", action="store_true", default=False,
                              help="Output in minimal format (key-value pairs only)")
    parameters_parser.add_argument("generators", type=str, nargs="*",
                                      help="Generator names to create config for")

    # box_yaml command
    box_yaml_parser = subparsers.add_parser("box_yaml", help="Create boxes from YAML configuration")
    box_yaml_parser.add_argument("yaml_file", type=str, help="YAML configuration file")
    box_yaml_parser.add_argument("--output-dir", type=str, default=".",
                                 help="Output directory (default: current directory)")

    # merge command
    merge_parser = subparsers.add_parser("merge", help="Merge multiple SVG files")
    merge_parser.add_argument("merge_args", nargs=argparse.REMAINDER,
                              help="Merge parameters")

    # examples command
    examples_parser = subparsers.add_parser("examples", help="Generate example SVGs")
    examples_parser.add_argument("--examples", action="store_true", default=False,
                                 help="Use the default examples.yml configuration file")
    examples_parser.add_argument("config", type=str, nargs="*",
                                 help="Path(s) to examples YAML configuration file(s)")
    examples_parser.add_argument("--dir", type=str, default="examples",
                                 help="Output directory (default: examples)")

    # Parse all arguments
    args = parser.parse_args(argv)

    # Set up logging based on global flags
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    # Route to the appropriate command handler
    if args.command == "build":
        cmd_build(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "parameters":
        if not args.all and not args.generators:
            parameters_parser.error("Either provide generator name(s) or use --all flag")
        cmd_parameters(args)
    elif args.command == "box_yaml":
        cmd_box_yaml(args)
    elif args.command == "merge":
        cmd_merge(args)
    elif args.command == "examples":
        if not args.examples and not args.config:
            examples_parser.error("Either provide config file(s) or use --examples flag")
        cmd_examples(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])

