from flask import Flask, render_template, request, redirect, url_for, Blueprint
import os
import sys
import glob
import random
import numpy as np
import pandas as pd

app = Flask(__name__)
app.template_folder = "web_data_annotator/templates"
app.static_folder = "web_data_annotator/static"
add_app = Blueprint("images", __name__, static_url_path='/frames', static_folder='./frames')
app.register_blueprint(add_app)

def load_data():
    if os.path.exists(OUTPUT_FILE):
        #data = pd.read_csv(OUTPUT_FILE, encoding='cp932', low_memory=False)
        data = pd.read_csv(OUTPUT_FILE, encoding='utf-8', low_memory=False)
        if os.path.exists(REF_FILE):
            #ref_data = pd.read_csv(REF_FILE, encoding='cp932', low_memory=False,
            ref_data = pd.read_csv(REF_FILE, encoding='utf-8', low_memory=False,
                                   dtype={'volume': int, 'page': int, 'frame': int})
            data = pd.concat([ref_data, data]).drop_duplicates("ID", keep="last").reset_index(drop=True)
        return data#.reindex(columns=COLUMNS)
    elif os.path.exists(REF_FILE):
        #return pd.read_csv(REF_FILE, encoding='cp932',
        return pd.read_csv(REF_FILE, encoding='utf-8',
                           dtype={'volume': int, 'page': int, 'frame': int})
    else:
        print("please check path to the reference csv.")
        sys.exit()

@app.route("/", methods=["GET", "POST"])
def index():
    data = load_data()
    #data.to_csv("web_data_annotator/tmp.csv", index=False, encoding='cp932')
    data.to_csv("web_data_annotator/tmp.csv", index=False, encoding='utf-8')

    # Manage image ID and its process-count
    image_paths = []
    image_names = []
    for folder in FOLDER_PATH_LIST:
        #image_path_list = sorted(glob.glob(root_folder_path + os.sep + folder + os.sep + "*"))
        image_path_list = sorted(glob.glob(os.path.join(root_folder_path, folder, "*")))
        image_paths.extend(image_path_list)
        image_name_list = [os.path.splitext(os.path.basename(p))[0] for p in image_path_list]
        image_names.extend(image_name_list)

    # Merge with existing data
    existing_IDs = set(data["ID"]) if not data.empty else set()
    current_IDs = set(image_names)
    new_IDs = current_IDs - existing_IDs
    if new_IDs:
        new_IDs = sorted(list(new_IDs))
        new_rows = pd.DataFrame([{"ID": ids, "annotation_count": 0} for ids in new_IDs])
        data = pd.concat([data, new_rows], ignore_index=True)
        data = data.sort_values("ID")
        #data.to_csv(OUTPUT_FILE, index=False, encoding='cp932')
        data.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

    if request.method == "POST":
        print("Form Data Received:", dict(request.form))
        form_data = dict(request.form)
        current_image_name = form_data.get("current_image")
        if not current_image_name:
            print("No images found.")
            sys.exit()
            #return redirect(url_for("index"))

        # Process form data
        row = data[data["ID"] == current_image_name]
        form_data[f"ID"] = form_data.pop("current_image")
        form_data[f"annotation_count"] = int(row.reset_index().loc[0, 'annotation_count'] + 1)\
            if pd.notna(row.reset_index().loc[0, 'annotation_count']) else 1
        form_data[f"balloon_num"] = int(sum(1 for key in form_data if key.startswith('balloon_text_')))
        form_data[f"outer_num"] = int(sum(1 for key in form_data if key.startswith('outer_text_')))
        form_data[f"background_num"] = int(sum(1 for key in form_data if key.startswith('background_text_')))
        form_data[f"character_num"] = int(sum(1 for key in form_data if key.startswith('character_who_')))
        print(form_data)
        
        # Update DataFrame
        if current_image_name in data["ID"].values:
            data.loc[data["ID"] == current_image_name, list(form_data.keys())] = list(form_data.values())
            #print("found: ", data.loc[data["ID"] == current_image_name, list(form_data.keys())])
            #print(list(form_data.keys()))
            #print(list(form_data.values()))
        else:
            new_row = {"ID": current_image_name, **form_data}
            data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)
            print("new: ", data.loc[data["ID"] == current_image_name, list(form_data.keys())])

        #data.to_csv(OUTPUT_FILE, index=False, encoding='cp932')
        data.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
        return redirect(url_for("index"))

    # Calculate progress
    total_ids = len(current_IDs)
    step1_count = data[data["annotation_count"] == 1].shape[0]
    step2_count = data[data["annotation_count"] == 2].shape[0]
    step1_progress = round((step1_count / total_ids) * 100, 2) if total_ids else 0
    step2_progress = round((step2_count / total_ids) * 100, 2) if total_ids else 0

    # Select next image
    remaining_images = data[data["annotation_count"] < 2]["ID"].tolist()
    if not remaining_images:
        return "Annotation completed."
    
    selected_image = image_paths[image_names.index(random.choice(remaining_images))]
    image_name = os.path.splitext(os.path.basename(selected_image))[0]
    current_idx = image_names.index(image_name)
    print(selected_image)
    print(image_name)
    prev_image = image_paths[current_idx - 1]
    next_image = image_paths[(current_idx + 1) % (len(image_paths) - 1)]
    print(prev_image)
    print(next_image)

    # Get initial data
    existing_row = data[data["ID"] == image_name].iloc[0] if not data[data["ID"] == image_name].empty else pd.Series()
    balloon_num = int(sum(1 for col in existing_row.index if col.startswith("balloon_text_") and not pd.isna(existing_row[col])))
    outer_num = int(sum(1 for col in existing_row.index if col.startswith("outer_text_") and not pd.isna(existing_row[col])))
    background_num = int(sum(1 for col in existing_row.index if col.startswith("background_text_") and not pd.isna(existing_row[col])))
    character_num = int(sum(1 for col in existing_row.index if col.startswith("character_who_") and not pd.isna(existing_row[col])))
    initial_data = existing_row.to_dict()
    
    print(balloon_num, outer_num, background_num, character_num)
    #print(initial_data)
    
    return render_template("base.html",
                           current_image=selected_image,
                           image_name=image_name,
                           prev_image=prev_image,
                           next_image=next_image,
                           initial_data=initial_data, balloon_num=balloon_num,
                           outer_num=outer_num, background_num=background_num, character_num=character_num,
                           step1_progress=step1_progress, step2_progress=step2_progress)

if __name__ == "__main__":
    root_folder_path = "./frames"
    if "nt" in os.name:
        root_folder_path = r"frames"
    exception = ["2019", "2020", "2021", "2022", "2023", "2024", "2025",
                 "CB01", "CB02", "CB03", "CB04", 
                 "Lapin", "Soleil", "Etoile"] # exception folder name list
    #FOLDER_PATH_LIST = os.listdir(root_folder_path) # 001 - 012, CB001 - CB004, 2019 - 2025, etc
    #FOLDER_PATH_LIST = sorted(list(set(FOLDER_PATH_LIST) - set(exception)))
    FOLDER_PATH_LIST = sorted([f for f in os.listdir(root_folder_path) if f not in exception])
    
    OUTPUT_FOLDER = "web_data_annotator"
    OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, "output.csv")
    REF_FILE = os.path.join(OUTPUT_FOLDER, "gochiusa_annotation.csv")
    
    COLUMNS = ["ID", "annotation_count", "reliability", "volume", "page", "frame", 
               "balloon_num", "outer_num", "background_num", "character_num"] + \
              [f"balloon_text_{i}" for i in range(1, 11)] + \
              [f"balloon_speaker_{i}" for i in range(1, 11)] + \
              [f"balloon_listener_{i}" for i in range(1, 11)] + \
              [f"balloon_shape_{i}" for i in range(1, 11)] + \
              [f"outer_text_{i}" for i in range(1, 11)] + \
              [f"outer_owner_{i}" for i in range(1, 11)] + \
              [f"outer_type_{i}" for i in range(1, 11)] + \
              [f"background_text_{i}" for i in range(1, 11)] + \
              [f"background_media_{i}" for i in range(1, 11)] + \
              [f"character_who_{i}" for i in range(1, 16)] + \
              [f"character_face_direction_{i}" for i in range(1, 16)] + \
              [f"character_behavior_a_{i}" for i in range(1, 16)] + \
              [f"character_behavior_b_{i}" for i in range(1, 16)]
    #data = pd.read_csv(OUTPUT_FILE, encoding='cp932', low_memory=False)
    #data.to_csv("web_data_annotator/output_utf8.csv", index=False, encoding='utf-8')
    #data = pd.read_csv("web_data_annotator/output_utf8.csv", encoding='utf-8')
    #sys.exit()
    app.run(debug=True)
