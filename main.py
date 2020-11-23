import segmentation
import fitparse

fitfile = fitparse.FitFile("./fit_files/alpes.fit")
segmentation.transform_fit_into_segments(fitfile)