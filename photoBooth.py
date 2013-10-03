#!/usr/bin/python
# -*- coding: utf-8 -*-

# Daniel Nelson
# https://github.com/danelson

import cv2
import optparse
import numpy
import scipy.ndimage

import imgutil


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
                        
        self.activeEffects = [] #array holding active effects
        self.numPyArray = None #the current array
        self.lastArray = None #the array from the previous frame
        
        self.rotDegree = 0
        self.gradientSigma = 0
        self.gaussianSigma = 0		

    def negate(self):
        '''
        Negates the image.
        '''
        new = numpy.ones_like(self.numPyArray)
        new = new*255
        negative = new - self.numPyArray
        self.numPyArray = negative
    
    def grayscale(self):
        '''
        Takes the grayscale of the image.
        '''
        self.numPyArray.astype(float)
        #for each color channel
        for i in range(3):
            self.numPyArray[:,:,i] = self.numPyArray[:,:,0]*0.3 + \
                                    self.numPyArray[:,:,1]*0.59 + \
                                    self.numPyArray[:,:,2]*0.11

    def flip_vertical(self):
        '''
        Flips the array over the vertical axis.
        '''
        self.numPyArray = numpy.fliplr(self.numPyArray)
        
    def flip_horizontal(self):
        '''
        Flips the array over the horizontal axis.
        '''
        self.numPyArray = numpy.flipud(self.numPyArray)
    

    def gaussian(self):
        '''
        Applies gaussian blur to the image. Takes a parameter from the
        command line.
        '''
        if self.gaussianSigma == 0:
            self.gaussianSigma = int(raw_input("Input gaussian sigma: "))
        for i in range(3):
            scipy.ndimage.filters.gaussian_filter(self.numPyArray[:,:,i],
                                                self.gaussianSigma,
                                                output=self.numPyArray[:,:,i])
    

    def gradient_magnitude(self):
        '''
        Applies the gradient magnitude to the image. Takes a parameter
        from the command line
        '''
        if self.gradientSigma == 0:
            self.gradientSigma = int(raw_input("Input gradeint sigma: "))
        for i in range(3):
            scipy.ndimage.filters.gaussian_gradient_magnitude(self.numPyArray[:,:,i],
                                                        self.gradientSigma,
                                                        output=self.numPyArray[:,:,i])

    def mirror(self):
        '''
        Mirrors the image vertically along the midpoint.
        '''
        numCols = self.numPyArray.shape[1]
        half = self.numPyArray[:,:numCols/2,:]
        halfFlip = numpy.fliplr(half)
        self.numPyArray[:,numCols/2:,:] = halfFlip
    
    
    def unsharp_mask(self):
        '''
        Sharpens the image. Takes a command line parameter for the
        gaussian sigma value.
        '''
        original = self.numPyArray.copy()
        self.gaussian() #makes self.numPyArray blurry
        highPass = original - self.numPyArray
        self.numPyArray = highPass*3 + original
        
        #get rid of the noise
        self.numPyArray[self.numPyArray > 255] = 255
        self.numPyArray[self.numPyArray < 0] = 0

    def laplace(self):
        '''  
        Applies laplace filter to the image.
        '''
        for i in range(3):
            scipy.ndimage.filters.laplace(self.numPyArray[:,:,i],
                                            output=self.numPyArray[:,:,i])
    

    def rotate(self):
        '''
        Rotates the image. Takes a command line parameter for the
        rotation degree.
        '''
        if self.rotDegree == 0:
            self.rotDegree = int(raw_input("Input rotation degree: "))
        scipy.ndimage.interpolation.rotate(self.numPyArray, self.rotDegree,
                                        reshape=False,output=self.numPyArray)

    def alpha_blend(self):
        '''
        Blends the image with the previous frame.
        '''
        self.numPyArray = self.numPyArray*0.1 + (1-0.1)*self.lastArray
    
    def frame_differencing(self):
        '''
        Applies frame differencing to the image.
        '''
        self.numPyArray = self.numPyArray - self.lastArrayA
        
        #correct for webcam error
        #self.numPyArray[self.numPyArray < 10] = 0
    
    def apply_effects(self):
        '''
        Applies the active effects.
        '''
        for x in self.activeEffects:
            self.effects.get(x)()
    
    def print_active_effects(self):
        '''
        Prints the active effects.
        '''
        if len(self.activeEffects) == 0:
            print "No active effects"
        else:
            print "Active effects: ", self.activeEffects

    def add_effects(self,char):
        '''
        Adds effects to the holder array.
        '''
        self.activeEffects.append(char)
    
    def remove_effects(self,char):
        '''
        Removes effects from the holder array.
        '''
        self.activeEffects.remove(char)
        if char == "r":
            self.rotDegree = 0
        elif char == "c":
            self.gradientSigma = 0
        elif char =="a":
            self.gaussianSigma = 0
    
    
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
        imgNum = 0
        #while the key being pushed isn't the exit button
        while key != 27:
            frame = self.source.read()[1]
            
            self.numPyArray = frame
            self.numPyArray = self.numPyArray.astype(numpy.float32)

            key = cv2.waitKey(30)

            #check if the key exists
            char = chr(key) if key > 0 else None
            if self.effects.has_key(char):
                #if the effect is not applied, queue to add it
                if char not in self.activeEffects:
                    self.add_effects(char)
                    self.print_active_effects()
                #if the effect is applied, queue to remove it
                else:
                    self.remove_effects(char)
                    self.print_active_effects()
                        
            #apply effects and show the image
            self.lastArrayB = self.numPyArray
            self.apply_effects()
            self.lastArrayA = self.numPyArray # save the this frame as last
            finalImage = imgutil.normalize(self.numPyArray)
            
            #if the key is the 'save' key
            if char == "s":
                imgNum += 1
                name = "img" + str(imgNum) + ".jpg"
                cv2.imwrite(name,finalImage)
            
            #show the image with effects active
            cv2.imshow("PhotoBooth", finalImage)
    


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
