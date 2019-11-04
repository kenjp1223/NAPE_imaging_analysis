#!/usr/bin/env python
# coding: utf-8

# # Code to evaluate and compare 2p imaging motion correction
# 
# author: Zhe Charles Zhou (UW NAPE Center)
# 
# Loads in raw and motion corrected data then computes:
# 
# - correlation to mean (CM) metric for all datasets
# - Crispness metric
# 
# pre-req input data:
# 
# - raw imaging data in form of h5
# - motion corrected data in form of h5

# In[32]:


import tifffile as tiff
import h5py
import os
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import math

from collections import defaultdict


# In[33]:


root_filename = 'VJ_OFCVTA_7_260_D6'
root_filename = 'itp_lhganiii_bl3_935'
#root_filename = '091618 155a day 2 tiffs'

folder = 'C:\\2pData\\Vijay data\\VJ_OFCVTA_7_D8_trained\\'
folder = 'C:\\2pData\\Ivan\\itp_lhganiii_bl3_678\\'
#folder = 'C:\\2pData\\Christian data\\Same FOV\\Individual Trials\\091618 155a day 2 tiffs\\processed\\'

fps = 5


# In[34]:


# make a dict with entries for each data/motion-correction type

dat_type_names = ['raw','sima','suite2p','caiman']
dat_ext = ['','_sima_mc','_suite2p_mc','_fullcaiman_mc']

tree = lambda: defaultdict(tree)
dat_dict = tree()

for idx,dat_type in enumerate(dat_type_names):
    dat_dict[dat_type]['dir'] = os.path.join( folder, '{}{}.h5'.format(root_filename,dat_ext[idx]) )

dat_dict


# In[35]:


# function to load tiff data and get data shape
def read_shape_tiff(data_path):
    
    data = tiff.imread(data_path).astype('int16')
    data_shape = data.shape
    
    print("{} {}".format(data.dtype, data.shape))
    
    return data, data_shape

def read_shape_h5(data_path):
    
    # open h5 to read, find data key, grab data, then close
    h5 = h5py.File(data_path,'r')
    data = np.squeeze(np.array( h5[h5.keys()[0]] )).astype('int16') # np.array loads all data into memory
    h5.close()
    
    data_shape = data.shape
    
    print("{} {}".format(data.dtype, data.shape))
    
    return data, data_shape


# In[36]:


# load data 
raw_dat, raw_dat_dim = read_shape_h5(dat_dict['raw']['dir'])
sima_dat, sima_dat_dim = read_shape_h5(dat_dict['sima']['dir'])
suite2p_dat, suite2p_dim = read_shape_h5(dat_dict['suite2p']['dir'])
suite2p_dat = suite2p_dat * 2 # needed b/c suite2p divides intensity values by 2

caiman_dat, caiman_dim = read_shape_h5(dat_dict['caiman']['dir'])


# In[37]:


# calculate minimum and max FOVs after motion correction to crop all data to similar dimensions (to facilitate correlation)
min_ypix = np.min([raw_dat_dim[1], sima_dat_dim[1], suite2p_dim[1]])
min_xpix = np.min([raw_dat_dim[2], sima_dat_dim[2], suite2p_dim[2]])


# In[38]:


# function to crop frames equally on each side
def crop_center(img,cropx,cropy):
    z,y,x = img.shape
    startx = x//2-(cropx//2)
    starty = y//2-(cropy//2)    
    return img[:,starty:starty+cropy,startx:startx+cropx]


# In[39]:


# use function to crop videos
raw_dat = crop_center(raw_dat,min_xpix,min_ypix)
suite2p_dat = crop_center(suite2p_dat,min_xpix,min_ypix)
caiman_dat = crop_center(caiman_dat,min_xpix,min_ypix)


# # Perform correlation to mean image

# In[40]:


# calculate mean image
raw_mean = np.mean(raw_dat, axis=0)
sima_mean = np.mean(sima_dat, axis=0)
suite2p_mean = np.mean(suite2p_dat, axis=0)
caiman_mean = np.mean(caiman_dat, axis=0)


# In[41]:


# plot mean images

# set color intensity limits based on min and max of all data
clim = [ np.min([raw_mean,sima_mean,suite2p_mean,caiman_mean]), np.max([raw_mean,sima_mean,suite2p_mean,caiman_mean])-100 ]

fig, axs = plt.subplots(2, 4, figsize=(15, 10))

im0 = axs[0,0].imshow(raw_mean, cmap='gray')
axs[0,0].set_title('Raw', fontsize = 20)

im1 = axs[0,1].imshow(sima_mean, cmap='gray')
axs[0,1].set_title('SIMA Corrected', fontsize = 20)

im2 = axs[0,2].imshow(suite2p_mean, cmap='gray')
axs[0,2].set_title('Suite2p Corrected', fontsize = 20)

im3 = axs[0,3].imshow(caiman_mean, cmap='gray')
axs[0,3].set_title('Caiman Corrected', fontsize = 20)

im0.set_clim(vmin=clim[0], vmax=clim[1]); im1.set_clim(vmin=clim[0], vmax=clim[1]); 
im2.set_clim(vmin=clim[0], vmax=clim[1]); im3.set_clim(vmin=clim[0], vmax=clim[1])

zoom_window = [150,250,200,300] # [xmin, xmax, ymin, ymax]

im3 = axs[1,0].imshow(raw_mean, cmap='gray')
axs[1,0].set_title('Raw Zoom', fontsize = 20)
axs[1,0].axis(zoom_window)
axs[1,0].invert_yaxis()

im4 = axs[1,1].imshow(sima_mean, cmap='gray')
axs[1,1].set_title('SIMA Zoom', fontsize = 20)
axs[1,1].axis(zoom_window)
axs[1,1].invert_yaxis()

im5 = axs[1,2].imshow(suite2p_mean, cmap='gray')
axs[1,2].set_title('Suite2p Zoom', fontsize = 20)
axs[1,2].axis(zoom_window)
axs[1,2].invert_yaxis()

im6 = axs[1,3].imshow(caiman_mean, cmap='gray')
axs[1,3].set_title('Caiman Zoom', fontsize = 20)
axs[1,3].axis(zoom_window)
axs[1,3].invert_yaxis()

im3.set_clim(vmin=clim[0], vmax=clim[1]); im4.set_clim(vmin=clim[0], vmax=clim[1]); 
im5.set_clim(vmin=clim[0], vmax=clim[1]); im6.set_clim(vmin=clim[0], vmax=clim[1])

#fig.colorbar(im0)



# In[11]:


# function to compute frame-resolved correlation to reference mean image
def corr2_all_frames(data,ref):
    cor_all = np.empty([data.shape[0],])
    
    for iframe,frame in enumerate(data):
        print 'frame {0}\r'.format(iframe),
        cor_all[iframe] = np.corrcoef(np.ndarray.flatten(frame), np.ndarray.flatten(ref))[0,1] #  corr2(np.ndarray.flatten(frame), np.ndarray.flatten(ref)) # 
        
    return cor_all


# In[12]:


# run frame-by-frame correlation to mean image
print('Corr Raw Data')
raw_corr2 = corr2_all_frames(raw_dat,raw_mean)
print('Corr Sima Data')
sima_corr2 = corr2_all_frames(sima_dat,sima_mean)
print('Corr Suite2p Data')
suite2p_corr2 = corr2_all_frames(suite2p_dat,suite2p_mean)
print('Corr Caiman Data')
caiman_corr2 = corr2_all_frames(caiman_dat,caiman_mean)


# In[13]:


# plot correlation as function of time 
fig, ax = plt.subplots(1, 1, figsize=(10,5), sharey=True)

tvec = np.linspace(0,raw_dat_dim[0]/fps,raw_dat_dim[0])

plt.plot(tvec,raw_corr2)
plt.plot(tvec,sima_corr2)
plt.plot(tvec,suite2p_corr2)
plt.plot(tvec,caiman_corr2)
plt.xlabel('Time [s]', fontsize=20)
plt.ylabel('Pearson Correlation', fontsize=20)
plt.legend(dat_type_names);


# In[14]:


# calculate correlation means
raw_corr_mean = np.mean(raw_corr2)
sima_corr_mean = np.mean(sima_corr2)
suite2p_corr_mean = np.mean(suite2p_corr2)
caiman_corr_mean = np.mean(caiman_corr2)
corr_means = [raw_corr_mean, sima_corr_mean, suite2p_corr_mean, caiman_corr_mean]
display(corr_means)

# calculate SEMs
raw_corr_sem = np.std(raw_corr2)/math.sqrt(len(raw_corr2))
sima_corr_sem = np.std(sima_corr2)/math.sqrt(len(sima_corr2))
suite2p_corr_sem = np.std(suite2p_corr2)/math.sqrt(len(suite2p_corr2))
caiman_corr_sem = np.std(caiman_corr2)/math.sqrt(len(caiman_corr2))
corr_sems = [raw_corr_sem, sima_corr_sem, suite2p_corr_sem, caiman_corr_sem]
display(corr_sems)


# In[15]:


x_pos = np.arange(len(dat_type_names)) # find x tick locations for replacement with condition names

fig, ax = plt.subplots()
ax.bar(x_pos, corr_means, yerr=corr_sems, align='center', alpha=0.5, ecolor='black', capsize=10)
ax.set_ylim([ np.min(corr_means)-0.01, np.max(corr_means)+0.01 ])
ax.set_xticks(x_pos)
ax.set_xticklabels(dat_type_names, fontsize = 20)
ax.set_ylabel('Pearson Correlation', fontsize = 20);


# # Calculate Crispness
# 
# https://www.sciencedirect.com/science/article/pii/S0165027017302753#tbl0005

# In[16]:


# calculate gradient vector field; https://stackoverflow.com/questions/30079740/image-gradient-vector-field-in-python
import numpy as np
import matplotlib.pyplot as plt
from PIL import ImageFilter

I = np.flipud(sima_mean)
p = np.asarray(I)
w,h = I.shape
complex_y = complex(0,sima_dat_dim[1])
complex_x = complex(0,sima_dat_dim[2])
y, x = np.mgrid[0:h:complex_y, 0:w:complex_x] # CZ: end dimensions need to match input

dy, dx = np.gradient(p)
skip = (slice(None, None, 3), slice(None, None, 3))

fig, ax = plt.subplots(figsize=(12, 12))
im = ax.imshow(np.flipud(I), extent=[x.min(), x.max(), y.min(), y.max()]) # show original img
ax.quiver(x[skip], y[skip], dx[skip], dy[skip]) # plot vectors

ax.set(aspect=1, title='Quiver Plot')
ax.set_title('Quiver Plot', fontsize = 30)
ax.axis([150,250,150,250])
plt.show()


# In[17]:


# calculate entry-wise magnitude

# CZ: why use class?
# class that takes in gradient x and y vector components and has a method to calculate magnitude
class Vector(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def vector_mag(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5


# In[18]:


def calc_all_vect_mag(dy,dx):
    
    h_pix = dy.shape[0]
    w_pix = dy.shape[1]
    
    all_vect_mag = np.empty( [h_pix,w_pix] )
    
    for index, x in np.ndenumerate(dy):
    
        ycoord = index[0] 
        xcoord = index[1]
        comb_vect = Vector(dx[ycoord,xcoord], dy[ycoord,xcoord])
        all_vect_mag[ycoord,xcoord] = comb_vect.vector_mag()
    
    return all_vect_mag


# In[19]:


raw_mean.shape


# In[20]:


img_in = np.asarray(np.flipud(raw_mean))
dy, dx = np.gradient(img_in)

raw_grad_mag = calc_all_vect_mag(dy,dx)


# In[21]:


img_in = np.asarray(np.flipud(sima_mean))
dy, dx = np.gradient(img_in)

sima_grad_mag = calc_all_vect_mag(dy,dx)


# In[22]:


img_in = np.asarray(np.flipud(suite2p_mean))
dy, dx = np.gradient(img_in)

suite2p_grad_mag = calc_all_vect_mag(dy,dx)


# In[23]:


img_in = np.asarray(np.flipud(caiman_mean))
dy, dx = np.gradient(img_in)

caiman_grad_mag = calc_all_vect_mag(dy,dx)


# In[24]:


# calculate Frobenius norm
print 'raw Crispness: ' , np.linalg.norm(raw_grad_mag, ord = 'fro')
print 'sima Crispness: ' , np.linalg.norm(sima_grad_mag, ord = 'fro')
print 'suite2p Crispness: ' , np.linalg.norm(suite2p_grad_mag, ord = 'fro')
print 'caiman Crispness: ' , np.linalg.norm(caiman_grad_mag, ord = 'fro')


# # Perform KLT Tracking with OpenCV
# 
# Based on: https://docs.opencv.org/3.4/d4/dee/tutorial_optical_flow.html
# 
# Also informative: https://stackoverflow.com/questions/18863560/how-does-klt-work-in-opencv
# 
# https://www.learnopencv.com/object-tracking-using-opencv-cpp-python/

# In[ ]:


# grab reference frame
ref_frame = raw_dat[0,:,:]
this_frame = raw_dat[100,:,:]


# In[ ]:


# params for ShiTomasi corner detection
feature_params = dict( maxCorners = 10,
                       qualityLevel = 0.3,
                       minDistance = 7,
                       blockSize = 7 )
# Parameters for lucas kanade optical flow
lk_params = dict( winSize  = (15,15),
                  maxLevel = 2,
                  criteria = (cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 10, 0.03))


# In[ ]:


p0 = cv.goodFeaturesToTrack(ref_frame, mask = None, **feature_params)
p0.shape


# In[ ]:


# Create some random colors
color = np.random.randint(0,255,(100,3))
# Create a mask image for drawing purposes
mask = np.zeros_like(ref_frame)
frame_idx = 1

while(1):
    
    this_frame = raw_dat[frame_idx,:,:]
    
    # calculate optical flow
    p1, st, err = cv.calcOpticalFlowPyrLK(ref_frame, this_frame, p0, None, **lk_params)
    
    # Select good points
    good_new = p1[st==1]
    good_old = p0[st==1]
    
    # draw the tracks
    for i,(new,old) in enumerate(zip(good_new, good_old)):
        a,b = new.ravel()
        c,d = old.ravel()
        mask = cv.line(mask, (a,b),(c,d), color[i].tolist(), 2)
        frame = cv.circle(this_frame,(a,b),5,color[i].tolist(),-1)
    img = cv.add(this_frame,mask)
    cv.imshow('frame',img)
    k = cv.waitKey(30) & 0xff
    if k == 27 or frame_idx == raw_dat_dim[0]-1:
        break
    # Now update the previous frame and previous points
    old_gray = this_frame.copy()
    p0 = good_new.reshape(-1,1,2)
    
    frame_idx += 1



# In[ ]:




