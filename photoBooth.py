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
                        
        self.active_effects = [] #array holding active effects
        self.frame = None #the current array
        self.last_array = None #the array from the previous frame
        
        self.rotation_degree = 0
        self.gradient_sigma = 0
        self.gaussian_sigma = 0		

    def negate(self):
        '''
        Negates the image.
        '''
        new = numpy.ones_like(self.frame)
        new = new*255
        negative = new - self.frame
        self.frame = negative
    
    def grayscale(self):
        '''
        Takes the grayscale of the image.
        '''
        self.frame.astype(float)
        #for each color channel
        for i in range(3):
            self.frame[:,:,i] = self.frame[:,:,0]*0.3 + \
                                    self.frame[:,:,1]*0.59 + \
                                    self.frame[:,:,2]*0.11

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
            self.gaussian_sigma = int(raw_input("Input gaussian sigma: "))
        for i in range(3):
            scipy.ndimage.filters.gaussian_filter(self.frame[:,:,i],
                                                self.gaussian_sigma,
                                                output=self.frame[:,:,i])
    

    def gradient_magnitude(self):
        '''
        Applies the gradient magnitude to the image. Takes a parameter
        from the command line
        '''
        if self.gradient_sigma == 0:
            self.gradient_sigma = int(raw_input("Input gradeint sigma: "))
        for i in range(3):
            scipy.ndimage.filters.gaussian_gradient_magnitude(self.frame[:,:,i],
                                                        self.gradient_sigma,
                                                        output=self.frame[:,:,i])

    def mirror(self):
        '''
        Mirrors the image vertically along the midpoint.
        '''
        numCols = self.frame.shape[1]
        half = self.frame[:,:numCols/2,:]
        halfFlip = numpy.fliplr(half)
        self.frame[:,numCols/2:,:] = halfFlip
    
    
    def unsharp_mask(self):
        '''
        Sharpens the image. Takes a command line parameter for the
        gaussian sigma value.
        '''
        original = self.frame.copy()
        self.gaussian() #makes self.frame blurry
        highPass = original - self.frame
        self.frame = highPass*3 + original
        
        #get rid of the noise
        self.frame[self.frame > 255] = 255
        self.frame[self.frame < 0] = 0

    def laplace(self):
        '''  
        Applies laplace filter to the image.
        '''
        for i in range(3):
            scipy.ndimage.filters.laplace(self.frame[:,:,i],
                                            output=self.frame[:,:,i])
    

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
        self.frame = self.frame - self.lastArrayA
        
        #correct for webcam error
        #self.frame[self.frame < 10] = 0
    
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
            self.lastArrayB = self.frame
            self.apply_effects()
            self.lastArrayA = self.frame # save the this frame as last
            
            #if the key is the 'save' key
            if char == "s":
                frame_number += 1
                name = "img" + str(frame_number) + ".jpg"
                cv2.imwrite(name,self.frame)
            
            #show the image with effects active
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
