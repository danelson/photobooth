#!/usr/bin/python
# -*- coding: utf-8 -*-

# Daniel Nelson
# https://github.com/danelson

import cv2
import optparse
import numpy
import scipy.ndimage

class PhotoBooth(object):
    def __init__(self, source=0):
        '''
        Initialize a slide show with a directory containing jpg
        images. Image files with extensions .jpg and .JPG will be found.
        '''
        self.source = cv2.VideoCapture(source)
        
        self.effects = {"n":self.negate, "g":self.grayscale,
                "v":self.flip_vertical, "h":self.flip_horizontal,
                "a":self.gaussian, "l":self.laplace, "r":self.rotate,
                "m":self.mirror, "b":self.alpha_blend,
                "c":self.gradient_magnitude, "u":self.unsharp_mask,
                "f":self.frame_differencing}
                        
        self.active_effects = []
        self.frame = None
        self.previous_frame = None
        
        self.rotation_degree = 0
        self.gradient_sigma = 0
        self.gaussian_sigma = 0		

    def negate(self):
        '''
        Negates the image.
        '''
        new = numpy.ones_like(self.frame)
        new = new * 255
        negative = new - self.frame
        self.frame = negative
    
    def _grayscale(self, img):
        '''
        Takes the grayscale of the image.
        '''
        img.astype(float)
        #for each color channel
        for i in range(3):
            img[:,:,i] = img[:,:,0]*0.3 + \
                            img[:,:,1]*0.59 + \
                            img[:,:,2]*0.11
        return img
    
    def grayscale(self):
        '''
        Takes the grayscale of the image.
        '''
        self.frame = self._grayscale(self.frame)

    def flip_vertical(self):
        '''
        Flips the array over the vertical axis.
        '''
        self.frame = numpy.fliplr(self.frame)
        
    def flip_horizontal(self):
        '''
        Flips the array over the horizontal axis.
        '''
        self.frame = numpy.flipud(self.frame)
    
    def gaussian(self):
        '''
        Applies gaussian blur to the image. Takes a parameter from the
        command line.
        '''
        if self.gaussian_sigma == 0:
            self.gaussian_sigma = int(raw_input("Input Gaussian sigma: "))
        for i in range(3):
            scipy.ndimage.filters.gaussian_filter(self.frame[:,:,i],
                                                self.gaussian_sigma,
                                                output=self.frame[:,:,i])
    
    def gradient_magnitude(self):
        '''
        Applies the gradient magnitude to the image. Takes a parameter
        from the command line.
        '''
        if self.gradient_sigma == 0:
            self.gradient_sigma = int(raw_input("Input gradient sigma: "))
        for i in range(3):
            scipy.ndimage.filters.gaussian_gradient_magnitude(self.frame[:,:,i],
                                                        self.gradient_sigma,
                                                        output=self.frame[:,:,i])

    def mirror(self):
        '''
        Mirrors the image vertically along the midpoint.
        '''
        num_cols = self.frame.shape[1]
        half = self.frame[:,:num_cols/2,:]
        halfFlip = numpy.fliplr(half)
        self.frame[:,num_cols/2:,:] = halfFlip
    
    
    def unsharp_mask(self):
        '''
        Sharpens the image. Takes a command line parameter for the
        gaussian sigma value.
        '''
        original = self.frame.copy()
        self.gaussian()
        high_pass = original - self.frame
        self.frame = high_pass*3 + original
        
        # Clip values
        self.frame[self.frame > 255] = 255
        self.frame[self.frame < 0] = 0

    def laplace(self):
        '''  
        Applies laplace filter to the image.
        '''
        original = numpy.zeros_like(self.frame)
        for i in range(3):
            scipy.ndimage.filters.laplace(self.frame[:,:,i],
                                            output=original[:,:,i])
        
        self.frame = original
        
    def rotate(self):
        '''
        Rotates the image. Takes a command line parameter for the
        rotation degree.
        '''
        if self.rotation_degree == 0:
            self.rotation_degree = int(raw_input("Input rotation degree: "))
            
        scipy.ndimage.interpolation.rotate(self.frame, self.rotation_degree,
                                        reshape=False,output=self.frame)

    def alpha_blend(self):
        '''
        Blends the image with the previous frame.
        '''
        self.frame = self.frame*0.1 + (1-0.1)*self.last_array
    
    def frame_differencing(self):
        '''
        Applies frame differencing to the image.
        '''
        ### FIX THIS
        self.frame = self.normalize(self.frame - self.previous_frame)
    
    def apply_effects(self):
        '''
        Applies the active effects.
        '''
        for x in self.active_effects:
            self.effects.get(x)()
    
    def print_active_effects(self):
        '''
        Prints the active effects.
        '''
        if len(self.active_effects) == 0:
            print "No active effects"
        else:
            print "Active effects: ", self.active_effects

    def add_effects(self,char):
        '''
        Adds effects to the holder array.
        '''
        self.active_effects.append(char)
    
    def remove_effects(self,char):
        '''
        Removes effects from the holder array.
        '''
        self.active_effects.remove(char)
        if char == "r":
            self.rotation_degree = 0
        elif char == "c":
            self.gradient_sigma = 0
        elif char =="a":
            self.gaussian_sigma = 0
    
    def normalize(self, image, range_=(0,255), dtype=numpy.uint8):
        '''
        Linearly remap values in input data into range (0-255, by default).  
        Returns the dtype result of the normalization (numpy.uint8 by default).
        '''
        # find input and output range of data
        if isinstance(range_, (int, float, long)):
            minOut, maxOut = 0., float(range_)
        else:
            minOut, maxOut = float(range_[0]), float(range_[1])
        minIn, maxIn = image.min(), image.max()
        ratio = (maxOut - minOut) / (maxIn - minIn)
        
        # remap data
        output = (image - minIn) * ratio + minOut
        
        return output.astype(dtype)
    
    def run(self):
        '''
        # Converts the image, takes key strokes and displays the
        image in a window.
        
        Run the photobooth, displaying either a video or camera.
        n negative
        g grayscale
        v vertical flip
        h horizontal flip
        a gaussian blur
        l laplace
        r rotate
        m mirror
        b alpha blend
        c gradient magnitude
        u unsharp mask
        f frame differencing
        esc
        '''
        key = None
        frame_number = 0
        
        
        #while the key being pushed isn't the exit button
        while key != 27:
            self.frame = self.source.read()[1]
            self.frame = self.frame.astype(numpy.float32)
            
            key = cv2.waitKey(30)

            # Check if the key exists
            char = chr(key) if key > 0 else None
            if self.effects.has_key(char):
                #if the effect is not applied, queue to add it
                if char not in self.active_effects:
                    self.add_effects(char)
                    self.print_active_effects()
                #if the effect is applied, queue to remove it
                else:
                    self.remove_effects(char)
                    self.print_active_effects()
                        
            #apply effects and show the image
            self.apply_effects()
            self.previous_frame = self.frame.copy() # save the this frame as last
            self.frame = self.normalize(self.frame)
            
            # Save the image
            if char == "s":
                frame_number += 1
                name = "img" + str(frame_number) + ".jpg"
                name = "img-{0:05d}.jpg".format(frame_number)
                cv2.imwrite(name,self.frame)
            
            cv2.imshow("PhotoBooth", self.frame)
    


#####################################################################
#####################################################################

if __name__ == "__main__":
    # parse command line parameters
    parser = optparse.OptionParser()
    parser.add_option("-s", "--source",
                        help="0-9 for webcam or video file path",
                        default=0, type="int")
    options, remain = parser.parse_args()

    # launch photo booth
    show = PhotoBooth(options.source)
    show.run()
