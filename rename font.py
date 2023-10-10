import os
import sys
from fontTools import ttLib

# Utilities

def file_exists(filepath):
    """Tests for existence of a file on the string filepath"""
    return os.path.exists(filepath) and os.path.isfile(filepath)

def bulk_rename_fonts(folder_path, user_input):
    for filename in os.listdir(folder_path):
        if filename.endswith(('.otf', '.ttf', '.woff', '.woff2')):
            font_path = os.path.join(folder_path, filename)
            
            if not file_exists(font_path):
                sys.stderr.write(
                    f"[fontname.py] ERROR: the path '{font_path}' does not appear to be a valid file path.{os.linesep}"
                )
                continue
            
            try:
                tt = ttLib.TTFont(font_path)
                namerecord_list = tt["name"].names
                
                style = ""
                
                # determine font style for this file path from name record nameID 2
                for record in namerecord_list:
                    if record.nameID == 2:
                        style = str(record)
                        break
                
                # test that a style name was found in the OpenType tables of the font
                if len(style) == 0:
                    sys.stderr.write(
                        f"[fontname.py] Unable to detect the font style from the OpenType name table in '{font_path}'. {os.linesep}"
                    )
                    sys.stderr.write("Skipping renaming for this font.")
                    continue
                else:
                    # used for the Postscript name in the name table (no spaces allowed)
                    postscript_font_name = f"{user_input}_{filename.replace(' ', '')}"
                    # font family name
                    nameID1_string = f"{user_input}_{filename}"
                    nameID16_string = f"{user_input}_{filename}"
                    # full font name
                    nameID4_string = f"{user_input}_{filename} {style}"
                    # Postscript name
                    # - no spaces allowed in family name or the PostScript suffix. should be dash delimited
                    nameID6_string = f"{postscript_font_name}-{style.replace(' ', '')}"
                    
                    # modify the opentype table data in memory with updated values
                    for record in namerecord_list:
                        if record.nameID == 1:
                            record.string = nameID1_string
                        elif record.nameID == 4:
                            record.string = nameID4_string
                        elif record.nameID == 6:
                            record.string = nameID6_string
                        elif record.nameID == 16:
                            record.string = nameID16_string
                    
                    # CFF table naming for CFF fonts (only)
                    if "CFF " in tt:
                        try:
                            cff = tt["CFF "]
                            cff.cff[0].FamilyName = nameID1_string
                            cff.cff[0].FullName = nameID4_string
                            cff.cff.fontNames = [nameID6_string]
                        except Exception as e:
                            sys.stderr.write(
                                f"[fontname.py] ERROR: unable to write new names to CFF table: {e}"
                            )
                    
                    # write changes to the font file
                    try:
                        tt.save(font_path)
                        print(f"[OK] Updated '{font_path}' with the name '{nameID4_string}'")
                    except Exception as e:
                        sys.stderr.write(
                            f"[fontname.py] ERROR: unable to write new name to OpenType name table for '{font_path}'. {os.linesep}"
                        )
                        sys.stderr.write(f"{e}{os.linesep}")
            except Exception as e:
                sys.stderr.write(
                    f"[fontname.py] ERROR: Unable to process font '{font_path}': {e}{os.linesep}"
                )
                sys.stderr.write("Skipping renaming for this font.")
                continue

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.stderr.write(
            "Usage: python3 fontname.py [FOLDER_PATH] [USER_INPUT]\n"
        )
        sys.exit(1)

    folder_path = sys.argv[1]
    user_input = sys.argv[2]

    if not os.path.isdir(folder_path):
        sys.stderr.write(
            f"[fontname.py] ERROR: the path '{folder_path}' is not a valid folder.{os.linesep}"
        )
        sys.exit(1)

    bulk_rename_fonts(folder_path, user_input)
