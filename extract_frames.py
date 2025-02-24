# -*- coding: utf-8 -*-

import numpy as np
import os, sys
import re
import pathlib
import glob
import cv2
from tqdm import tqdm
import time
import matplotlib.pyplot as plt

def extract_frames(img, roi_list, margin_size, DEBUG=False):
    ret, thresh = cv2.threshold(img, 32, 255, cv2.THRESH_BINARY)
    thresh = 255 - thresh # because the pixel value of the frames is approximately 0
    
    th_col_sum = np.mean(thresh, axis=0)
    th_row_sum = np.mean(thresh, axis=1)
    _, _, w, h = roi_list[0]

    def filter_groups(arr, margin, inverse=False):
        # [ 114  115  119  120  121  130  547  573  574 1003 1004 1005 1006]
        diff = np.diff(arr)
        # -> [  1   4   1   1   9 417  26   1 429   1   1   1]
        
        # Mark peaks where the distance is less than 5
        is_close = diff <= margin
        # -> [ True  True  True  True  True False False  True False  True  True  True]
        
        # Calculate the index of the group to which each element belongs.
        groups = np.cumsum(np.concatenate(([0], ~is_close)))
        # -> [0 0 0 0 0 0 1 2 2 3 3 3 3], where margin = 10

        # Get the first element of each group.
        unique_groups, group_indices = np.unique(groups, return_index=True)
        if inverse:
            group_indices = sum([[g-1, g] for g in group_indices[1:]], [])
        filtered_arr = arr[group_indices]
        # -> [ 114  547  573 1003]

        # Removed if there is only one group from the start.
        if len(unique_groups) == 1:
            return np.array([], dtype=arr.dtype)
        return filtered_arr#, prioritized

    def calc_peak_diff(peak, frame_length, eps):
        # extract upper/left line of the frames
        # use broadcast to calculate all the combination at once
        # a peak coordinate has [..., 561, 605, 936, 970, ...] for columns(S->I, 4 frames),
        # where 561/936 is upper/lower line of 2nd frame and height=375, so 605 should be removed.
        # Here, adding height to the true upper frame coordinate results in a value close to the corresponding lower frame coordinate.
        # np.min()+1 is a margin that reflects the variation in pixel values due to printing.
        # 605 is not a frame-constituting line, so it can be removed by this strategy.
        #print(peak, frame_length)
        #print(peak[:, None] - (peak + frame_length))
        diff = np.abs(peak[:, None] - (peak + frame_length))
        withins = diff <= np.min(diff)+eps
        # except the comparison of the same element
        np.fill_diagonal(withins, False)
        peak_list = peak[np.any(withins, axis=0)]
        return peak_list

    diff = np.diff(th_col_sum)
    diff[np.abs(diff)<16] = 0
    peak = ((diff[:-1] * diff[1:]) < 1) & (diff[:-1] > diff[1:]*5)
    peak = np.append(peak[-1], peak[:-1]) # shift
    peak = np.where(peak==1)[0]
    if len(peak)<1:
        return []
    prioritized_peak = np.where(th_col_sum>np.max(th_col_sum)*0.50)[0]
    inverse = False
    if len(prioritized_peak)>100: # black back-ground case
        inverse = True
    prioritized_peak = filter_groups(prioritized_peak, 5, inverse=inverse)
    diff = np.diff(prioritized_peak)
    if len(diff)<1:
        return []
    new_w = diff[np.argmin(np.abs(diff-w))]
    if new_w>w*1.05 or new_w<w*0.95:
        new_w = w
    x_list = calc_peak_diff(peak, new_w, 3)
    if len(x_list)<1:
        return []

    cnt = 0
    old_list = []
    while len(x_list)!=1 and len(x_list)!=2 or cnt==0:
        if cnt>2:
            print("Error detected at Volume %s, Page % 03d. Please check the result." % (i, j+1))
            return []
        valid_indices = np.where(np.diff(x_list) > 10)[0]
        if len(valid_indices)<1:
            x_list = [x_list[0]]
            break
        x_list = x_list[np.append(valid_indices, valid_indices[-1] + 1)]
        peak_mod = calc_peak_diff(x_list, new_w+margin_size, 11-cnt*4)
        if len(peak_mod)<1:
            return []
        idx = np.where(x_list == peak_mod[-1])[0][0]
        if x_list[idx+1] - x_list[idx] < new_w+margin_size:
            x_list = np.append(peak_mod, x_list[-1])
        else:
            x_list = np.append(peak_mod, x_list[idx+1])
        if len(old_list)==len(x_list) and len(x_list)>0:
            # for cases where detection is not possible; e.g. 12-007
            diff = np.diff(x_list, 2)
            unique, freq = np.unique(diff, return_counts=True)
            w_margin = unique[np.argmax(freq)] # mode
            x_list = [x_list[0]+w_margin*(n+1) for n in range(len(x_list)+1)]
            x_list = np.array(x_list)
        cnt += 1
        diff = np.abs(peak[:, None] - (peak + w))

    diff = np.diff(th_row_sum)
    diff[np.abs(diff)<16] = 0
    peak = ((diff[:-1] * diff[1:]) < 1) & (diff[:-1] > diff[1:]*5)
    peak = np.append(peak[-1], peak[:-1])
    peak = np.where(peak==1)[0]
    if len(peak)<2:
        return []
    prioritized_peak = np.where(th_row_sum>np.max(th_row_sum)*0.50)[0]
    inverse = False
    if len(prioritized_peak)>100: # black back-ground case
        inverse = True
    prioritized_peak = filter_groups(prioritized_peak, 5, inverse=inverse)
    diff = np.diff(prioritized_peak)
    if len(diff)<2:
        return []
    new_h = diff[np.argmin(np.abs(diff-h))]
    if new_h>h*1.05 or new_h<h*0.95:
        new_h = h
    y_list = calc_peak_diff(peak, new_h, 3)
    if len(y_list)<2:
        return []
    cnt = 0
    old_list = []
    while len(y_list)!=2 and len(y_list)!=4 or cnt==0:
        if cnt>2:
            print("Error detected at Volume %s, Page % 03d. Please check the result." % (i, j+1))
            return []
        valid_indices = np.where(np.diff(y_list) > 10)[0]
        if len(valid_indices)<1:
            return []
        y_list = y_list[np.append(valid_indices, valid_indices[-1] + 1)]
        peak_mod = calc_peak_diff(y_list, new_h+margin_size, 11-cnt*4)
        if len(peak_mod)<1:
            return []
        idx = np.where(y_list == peak_mod[-1])[0][0]
        if y_list[idx+1] - y_list[idx] < new_h+margin_size:
            y_list = np.append(peak_mod, y_list[-1])
        else:
            y_list = np.append(peak_mod, y_list[idx+1])
        if cnt>1 and len(old_list)==len(y_list) and len(y_list)>0:
            # for cases where detection is not possible; e.g. 12-007
            diff = np.diff(y_list)
            unique, freq = np.unique(diff, return_counts=True)
            h_margin = unique[np.argmax(freq)] # mode
            y_list = [y_list[0]+h_margin*n for n in range(len(y_list)+1)]
            y_list = np.array(y_list)
        cnt += 1
        old_list = y_list
    
    x_list = sorted(x_list, reverse=True) # reading order; R->L
    new_roi_list = [[x, y, w, h] for x in x_list for y in y_list]
    return new_roi_list

def find_rectangles(img, margin_size):
    start = time.time()
    roi_list = []
    ret, thresh = cv2.threshold(img, 32, 255, cv2.THRESH_BINARY)
    thresh = 255 - thresh # because the pixel value of the frames is approximately 0
    # see https://labs.eecs.tottori-u.ac.jp/sd/Member/oyamada/OpenCV/html/py_tutorials/py_imgproc/py_thresholding/py_thresholding.html
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) == 4 and area > 10000 and area < 500000: # p.6 of vol.1 has ~137,000
            x, y, w, h = cv2.boundingRect(cnt)
            roi_list.append([x, y, w, h])

    if len(roi_list)==0: # e.g. cover, character page, etc
        return roi_list

    new_roi_list = modify_roi_list(roi_list, margin_size)
    return new_roi_list

def extract_unique(roi_list, dim, margin_size):
    old = sorted([i[dim] for i in roi_list])
    new = [old[0]]
    for i in range(1, len(old)):
        if abs(old[i] - new[-1]) > margin_size:
            new.append(old[i])
    return new

def modify_roi_list(roi_list, margin_size):
    """
    The function to rearrange roi_list in the reading order.
    """

    xx = extract_unique(roi_list, 0, margin_size) # len = 2
    xx = sorted(xx, reverse=True) # R -> L
    yy = extract_unique(roi_list, 1, margin_size) # len = 4 or 2
    ww = extract_unique(roi_list, 2, margin_size) # len = 1
    hh = extract_unique(roi_list, 3, margin_size) # len = 1
    
    new_roi_list = [[x, y, w, h] for x in xx for y in yy for w in ww for h in hh]
    
    return new_roi_list

def get_roi_dict(folder_path_list, root_folder_path, margin):
    roi_dict_L, roi_dict_R = {}, {}
    roi_list_L, roi_list_R = [], []
    for i in tqdm(folder_path_list):
        img_path_list = os.listdir(root_folder_path + os.sep + i)
        img_path_list = sorted(img_path_list)

        for j, img_path in enumerate(img_path_list):
            # search the page where 8 frames are fully detected
            img = cv2.imread(root_folder_path + os.sep + i + os.sep + img_path)

            # image sizes are different for comic(01-04/05-12), CB, and max(201908/201909-),
            # so roi_list needs to be created for each domain
            # comic: 1600x1127/1920x1352, CB: 2300x1629, max: 1920x1337/1938x1350
            if j==0:
                if i==folder_path_list[0]:
                    img_size = img.shape
                    img_size_str = "%dx%d" % (img_size[0], img_size[1])
                    if roi_dict_L.get(img_size_str) != None and roi_dict_R.get(img_size_str)!= None: # already obtained
                        break
                    
                if abs(img.shape[0]-img_size[0])>100 or abs(img.shape[0]/img.shape[1]-img_size[0]/img_size[1])>0.01:
                    img_size = img.shape
                    roi_list_L, roi_list_R = [], []
                margin_size = int(img_size[0]*margin)
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if len(roi_list_L)!=8 and j % 2 == 1: # odd-numbered pages; L
                roi_list_L = find_rectangles(gray, margin_size)
            elif len(roi_list_R)!=8 and j % 2 == 0: # even-numbered pages; R
                roi_list_R = find_rectangles(gray, margin_size)
            
            if len(roi_list_L)==8 and len(roi_list_R)==8:
                break
        
        if len(roi_list_L)==8 and len(roi_list_R)==8:
            img_size_str = "%dx%d" % (img_size[0], img_size[1])
            roi_dict_L[img_size_str] = roi_list_L
            roi_dict_R[img_size_str] = roi_list_R
    return roi_dict_L, roi_dict_R

if __name__ == '__main__':
    ##########  !!!!! change !!!!!  ##########
    root_folder_path = "../dataset/FUZ_new"
    new_folder_path = "./frames"
    if "nt" in os.name:
        root_folder_path = r"..\dataset\FUZ_new"
        new_folder_path = r".\frames"
    
    margin = 0.015625 # margin size of the extracted frame; 1600->25, 1920->30, 2300->35
    exception = ["Lapin", "Soleil", "Etoile"] # exception folder name list
    LATEST = False # Flag whether to process all data or only the latest data
    USE_TESSERACT = False
    DEBUG = False
    ##########  !!!!! change !!!!!  ##########

    
    
    folder_path_list = os.listdir(root_folder_path) # 001 - 012, CB001 - CB004, 2019 - 2025, etc
    folder_path_list = sorted(folder_path_list)
    folder_path_list = sorted(list(set(folder_path_list) - set(exception)))
    target_folder_path_list = folder_path_list
    if LATEST:
        target_folder_path_list = [folder_path_list[-1]]

    # search frames
    roi_dict_L, roi_dict_R = get_roi_dict(folder_path_list, root_folder_path, margin)
    
    # check the length of roi list
    for (key_L, value_L), (key_R, value_R) in zip(roi_dict_L.items(), roi_dict_R.items()):
        if len(value_L)!=8:
            print("The length of ROI_list_L doesn't correct for img_size of %s." % key_L)
            sys.exit()
        if len(value_R)!=8:
            print("The length of ROI_list_R doesn't correct for img_size of %s." % key_R)
            sys.exit()

    # crop frames
    for i in tqdm(target_folder_path_list):
        out_folder_path = new_folder_path + os.sep + i # ./frame/01
        os.makedirs(out_folder_path, exist_ok=True)

        img_path_list = os.listdir(root_folder_path + os.sep + i)
        img_path_list = sorted(img_path_list)
        
        for j, img_path in tqdm(enumerate(img_path_list), total=len(img_path_list)):
            name_base, ext = os.path.splitext(img_path)
            if re.findall(r"\d+", i)[0] in name_base[:-2]:
                out_img_name_base = out_folder_path + os.sep + name_base # ./frame/2019/201908_071
            else:
                out_img_name_base = out_folder_path + os.sep + i + "_" + name_base # ./frame/01/01_124
            
            img = cv2.imread(root_folder_path + os.sep + i + os.sep + img_path)

            if j==0:
                if i==target_folder_path_list[0]:
                    img_size = img.shape
                    margin_size = int(img_size[0]*margin)
                if abs(img.shape[0]-img_size[0])>100 or abs(img.shape[0]/img.shape[1]-img_size[0]/img_size[1])>0.01:
                    img_size = img.shape
                    margin_size = int(img_size[0]*margin)
                img_size_str = "%dx%d" % (img_size[0], img_size[1])
            
            if j % 2 == 1:
                roi_list = roi_dict_L[img_size_str]
            else:
                roi_list = roi_dict_R[img_size_str]
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            current_roi_list = extract_frames(gray, roi_list, margin_size, DEBUG)
            if len(current_roi_list)<4: # cover, character, interlude, etc.
                continue
            for n, roi in enumerate(current_roi_list):
                x, y, w, h = roi
                x, y, w, h = x-margin_size, y-margin_size, w+margin_size*2, h+margin_size*2 # add margin
                frame = gray[y:y+h, x:x+w]
                cv2.imwrite(out_img_name_base+"_%02d.jpg" % (n+1), frame) # ./frame/001/01_124_07.jpg
