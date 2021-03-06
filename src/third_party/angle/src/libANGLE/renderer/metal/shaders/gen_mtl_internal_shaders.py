#!/usr/bin/python
# Copyright 2019 The ANGLE Project Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# gen_mtl_internal_shaders.py:
#   Code generation for Metal backend's default shaders.
#   NOTE: don't run this script directly. Run scripts/run_code_generation.py.

import os
import sys
import json
from datetime import datetime

template_header_boilerplate = """// GENERATED FILE - DO NOT EDIT.
// Generated by {script_name}
//
// Copyright {copyright_year} The ANGLE Project Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
//
"""


# Convert content of a file to byte array and append to a header file.
# variable_name: name of C++ variable that will hold the file content as byte array.
# filename: the file whose content will be converted to C++ byte array.
# dest_src_file: destination header file that will contain the byte array.
def append_file_as_byte_array_string(variable_name, filename, dest_src_file):
    string = '// Generated from {0}:\n'.format(filename)
    string += 'constexpr\nunsigned char {0}[] = {{\n'.format(variable_name)
    bytes_ = open(filename, "rb").read()
    byteCounter = 0
    for byte in bytes_:
        if byteCounter == 0:
            string += "  "
        string += '0x{:02x}'.format(ord(byte)) + ","
        byteCounter += 1
        if byteCounter == 12:
            byteCounter = 0
            string += "\n"
        else:
            string += " "

    string += "\n};\n"

    string += 'constexpr\nsize_t {0}_len = sizeof({0});\n'.format(variable_name)

    with open(dest_src_file, "a") as out_file:
        out_file.write(string)


# Convert content of a file to byte array and store in a header file.
# variable_name: name of C++ variable that will hold the file content as byte array.
# copyright_comments: copyright comments
# filename: the file whose content will be converted to C++ byte array.
# dest_src_file: destination header file that will contain the byte array.
def store_file_as_byte_array_string(variable_name, copyright_comments, filename, dest_src_file):
    os.system("echo \"{0}\" > {1}".format(copyright_comments, dest_src_file))

    append_file_as_byte_array_string(variable_name, filename, dest_src_file)


# Convert content of a metallib to byte array and store in a header file, then include this header in
# mtl_default_shaders_autogen.inc.
# variable_name: name of C++ variable that will hold the file content as byte array.
# copyright_comments: copyright comments
# filename: the metallib file whose content will be converted to C++ byte array.
def store_metallib_as_byte_array_and_include(variable_name, copyright_comments, filename):
    array_autogen_filename = "{0}_autogen.inc".format(
        filename.replace('.metallib', '').replace('.', '_'))

    # Generate a header containing the file's content as C array.
    store_file_as_byte_array_string(variable_name, copyright_comments, filename,
                                    array_autogen_filename)

    # Include this file in mtl_default_shaders_autogen.inc
    # NOTE: filename already includes "compiled/"
    include_code = '#include "{0}"\n'.format(array_autogen_filename.replace('compiled/', ''))
    with open('compiled/mtl_default_shaders_autogen.inc', "a") as out_file:
        out_file.write(include_code)


# Compile metal shader.
# mac_version: target version of macOS
# ios_version: target version of iOS
# variable_name: name of C++ variable that will hold the compiled binary data as a C array.
# additional_flags: additional shader compiler flags
# src_files: metal source files
def gen_precompiled_shaders(mac_version, ios_version, variable_name, additional_flags, src_files,
                            copyright_comments):
    print('Generating default shaders with flags=\'{0}\' ...'.format(additional_flags))

    # Mac version's compilation
    print('Compiling macos {0} version of default shaders ...'.format(mac_version))

    mac_metallib = 'compiled/{0}.mac.metallib'.format(variable_name)

    object_files = ''
    for src_file in src_files:
        object_file = 'compiled/default.{0}.{1}.air'.format(mac_version, src_file)
        object_files += ' ' + object_file
        os.system('xcrun -sdk macosx metal -mmacosx-version-min={0} {1} {2} -c -o {3}'.format(
            mac_version, additional_flags, src_file, object_file))
    os.system('xcrun -sdk macosx metallib {object_files} -o {file}'.format(
        file=mac_metallib, object_files=object_files))

    # iOS device version's compilation
    print('Compiling ios {0} version of default shaders ...'.format(ios_version))

    ios_metallib = 'compiled/{0}.ios.metallib'.format(variable_name)

    object_files = ''
    for src_file in src_files:
        object_file = 'compiled/default.ios.{0}.{1}.air'.format(ios_version, src_file)
        object_files += ' ' + object_file
        os.system('xcrun -sdk iphoneos metal -mios-version-min={0} {1} {2} -c -o {3}'.format(
            ios_version, additional_flags, src_file, object_file))
    os.system('xcrun -sdk iphoneos metallib {object_files} -o {file}'.format(
        file=ios_metallib, object_files=object_files))

    # iOS simulator version's compilation
    print('Compiling ios {0} simulator version of default shaders ...'.format(ios_version))

    ios_sim_metallib = 'compiled/{0}.ios_sim.metallib'.format(variable_name)

    object_files = ''
    for src_file in src_files:
        object_file = 'compiled/default.ios_sim.{0}.{1}.air'.format(ios_version, src_file)
        object_files += ' ' + object_file
        os.system('xcrun -sdk iphonesimulator metal {0} {1} -c -o {2}'.format(
            additional_flags, src_file, object_file))
    os.system('xcrun -sdk iphonesimulator metallib {object_files} -o {file}'.format(
        file=ios_sim_metallib, object_files=object_files))

    # Mac version's byte array string
    os.system(
        'echo "#if TARGET_OS_OSX || TARGET_OS_MACCATALYST\n" >> compiled/mtl_default_shaders_autogen.inc'
    )
    store_metallib_as_byte_array_and_include(variable_name, copyright_comments, mac_metallib)

    # iOS simulator version's byte array string
    os.system(
        'echo "\n#elif TARGET_OS_IOS && TARGET_OS_SIMULATOR  // TARGET_OS_OSX || TARGET_OS_MACCATALYST\n" >> compiled/mtl_default_shaders_autogen.inc'
    )

    store_metallib_as_byte_array_and_include(variable_name, copyright_comments, ios_sim_metallib)

    # iOS version's byte array string
    os.system(
        'echo "\n#elif TARGET_OS_IOS  // TARGET_OS_OSX || TARGET_OS_MACCATALYST\n" >> compiled/mtl_default_shaders_autogen.inc'
    )

    store_metallib_as_byte_array_and_include(variable_name, copyright_comments, ios_metallib)

    os.system(
        'echo "#endif  // TARGET_OS_OSX || TARGET_OS_MACCATALYST\n" >> compiled/mtl_default_shaders_autogen.inc'
    )

    os.system('rm -rfv compiled/*.air')
    os.system('rm -rfv compiled/*.metallib')


def main():
    src_files = ['blit.metal', 'clear.metal', 'gen_indices.metal']

    # yapf: disable
    os_specific_autogen_files = [
        'compiled/compiled_default_metallib_2_1_debug_ios_autogen.inc',
        'compiled/compiled_default_metallib_2_1_debug_ios_sim_autogen.inc',
        'compiled/compiled_default_metallib_2_1_debug_mac_autogen.inc',
        'compiled/compiled_default_metallib_2_1_ios_autogen.inc',
        'compiled/compiled_default_metallib_2_1_ios_sim_autogen.inc',
        'compiled/compiled_default_metallib_2_1_mac_autogen.inc',
        'compiled/compiled_default_metallib_debug_ios_autogen.inc',
        'compiled/compiled_default_metallib_debug_ios_sim_autogen.inc',
        'compiled/compiled_default_metallib_debug_mac_autogen.inc',
        'compiled/compiled_default_metallib_ios_autogen.inc',
        'compiled/compiled_default_metallib_ios_sim_autogen.inc',
        'compiled/compiled_default_metallib_mac_autogen.inc',
    ]
    # yapf: enable

    # auto_script parameters.
    if len(sys.argv) > 1:
        inputs = src_files + ['common.h', 'constants.h']
        outputs = ['compiled/mtl_default_shaders_autogen.inc'] + os_specific_autogen_files

        if sys.argv[1] == 'inputs':
            print ','.join(inputs)
        elif sys.argv[1] == 'outputs':
            print ','.join(outputs)
        else:
            print('Invalid script parameters')
            return 1
        return 0

    os.chdir(sys.path[0])

    boilerplate_code = template_header_boilerplate.format(
        script_name=sys.argv[0], copyright_year=datetime.today().year)

    # -------- Compile shaders -----------
    # boilerplate code
    os.system("echo \"{0}\" > compiled/mtl_default_shaders_autogen.inc".format(boilerplate_code))
    os.system(
        'echo "// Compiled binary for Metal default shaders.\n\n" >> compiled/mtl_default_shaders_autogen.inc'
    )
    os.system(
        'echo "#include <TargetConditionals.h>\n\n" >> compiled/mtl_default_shaders_autogen.inc')

    os.system('echo "// clang-format off" >> compiled/mtl_default_shaders_autogen.inc')

    # pre-compiled shaders
    gen_precompiled_shaders(10.13, 11.0, 'compiled_default_metallib', '', src_files,
                            boilerplate_code)
    gen_precompiled_shaders(10.13, 11.0, 'compiled_default_metallib_debug',
                            '-gline-tables-only -MO', src_files, boilerplate_code)
    gen_precompiled_shaders(10.14, 12.0, 'compiled_default_metallib_2_1', '', src_files,
                            boilerplate_code)
    gen_precompiled_shaders(10.14, 12.0, 'compiled_default_metallib_2_1_debug',
                            '-gline-tables-only -MO', src_files, boilerplate_code)

    os.system('echo "// clang-format on" >> compiled/mtl_default_shaders_autogen.inc')


if __name__ == '__main__':
    sys.exit(main())
