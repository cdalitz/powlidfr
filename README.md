PowLiDFR: LiDAR Data Set of Power Lines
=======================================

This date set contains 25 LiDAR scenes taken from the LiDAR HD project of the
French Institut national de l’information géographique et forestière (IGN)
as published in May 2025. The samples have been chosen to cover a variety
of resolutions and problems for power line detection and have been manually
labeled.

Please cite the following article when using the data set:

> C. Dalitz, O., S. Goebbels, M. Shamsadini Motlagh, G. Gerzabek:
> "Power Line Detection in Point Clouds with Point-SAM and RANSAC."
> accepted for The International Conference on Computer Vision Theory
> and Applications (VISAPP) (2027)
> https://doi.org/10.48550/arXiv.2611.21438

The following sections describe the structure of the data set. Moreover,
a python implementation of the quality indices meanIOU and splits/misses etc.
is provided.

Data set structure
------------------

Each of the LiDAR scenes is stored in its own subfolder in data/.
Each subfolder contains four files: `*.la(s|z}`, `shift.csv`,
`pylons.csv`, and `duplicates.csv`.

### LiDAR point cloud `*.la(s|z)`

The point cloud in (compressed) LAS format. To avoid floating point
overflow, the coordintes have been centered around the point given
in the file `shift.csv`. The following ground truth labels are stored
in the Attribute `UserData`:

 - **0** for vegetation, ground, or any non-powerline background points.
 - **10** for pylons
 - **20** for power line points outside the region of interest
 - **31ff** for powerline segments with a distinct number for each line

The number of power lines in the region of interest is thus the highest
value for *UserData* minus 30.

## Pylon meta data `pylons.csv`

This file contains metadata for the pylons in the corresponding LiDAR scene.

| Column | Description |
| --- | --- |
| Mast | Pylon ID |
| X, Y | Center position of the pylon |
| Z_Bot | Height of the lowest cross-arm level |
| Z_Top | Height of the highest cross-arm level |
| Width | Horizontal arm width |
| EdgePoint1/2 (X/Y/Z) | The two outer corner points of the pylon structure. |

### Coordinate shift `shift.csv`

The LiDAR scenes use a global shift to minimize the impact of floating point
inaccuracies due to large coordinate magnitudes.

| Column | Meaning |
| --- | --- |
| shift_x | X-axis offset |
| shift_y | Y-axis offset |
| shift_z | Z-axis offset |

### Duplicate points `duplicates.csv`

The LiDAR HD data contain a sonsiderable number of duplicate points.
The coordinates of these points are given in this file. When there are
no duplicates, the file only contains the header line.

| Column | Meaning |
| --- | --- |
| x | x coordinate of duplicate |
| y | y coordinate of duplicate |
| z | z coordinate of duplicate |


Usage examples
--------------

Usage sample in R that counts the number of points per power line
and displays the scene:

```r
library(lidR)

# open file
scene <- "RIVENL61TARAS2"
file <- paste("data/", scene, "/", scene, ".laz", sep="")
las <- readLAS(file)

# number of points per line
las1 <- las[las$UserData >= 30]
x <- table(las$UserData)
print(x)

# 3D plot with rgl
print(plot(las, color="UserData", bg="gray"))
rgl::decorate3d(main=scene, box=F, axes=F, xlab="", ylab="", zlab="")
```

Usage sample in Python that counts the number of background and foreground
points:

```python
import laspy

# open file
scene = "RIVENL61TARAS2"
file = "data/" + scene + "/" + scene + ".laz"
las = laspy.read(file)

# count foreground and background points
fg = len(las.points[las.user_data > 30])
bg = len(las.points[las.user_data == 0])
```

Evaluation indices
------------------

The python source file `evaluate/evaluate.py` provides two functions
for computing the evaluation indices *mean(IoU)* and *segmentation error*
(splits, misses, merges) reported in the VISAPP paper. The functions
`meanIoU()` and `segmentation_error()` have the following arguments:

 - *points*
   Coordinates of all points
 - *G*
   Grund truth labels as an integer sequence of the same length as *points*.
   Points without labels can have labels `None`, `NA`, or `-1`. 
 - *S*
   Labels of test segmentation as an integer sequence of the same length as
   *points*. Points without labels can have labels `None`, `NA`, or `-1`. 

There is also a python script `compare_files.py` that demonstrates usage
of these functions. Example usage:

    python3 compare_files.py examples/G2.las examples/S2.las


Authors & Copyright
-------------------

Christoph Dalitz, Oskar Waedt, Mahdieh Shamsadini Motlagh, 2026
Institute for Pattern Recognition  
Niederrhein University of Applied Sciences  
Krefeld, Germany

The authors are grateful to the Institut national de l’information
géographique et forestière (IGN) for kindly publishing the LiDAR HD data
under a permissive license. Moreover they thank Gabriel Gerzabek for
selecting specific scenes from this this data set.

Permission is granted to copy, use, and modify the data set, provided
a reference to the following publication is given:

> C. Dalitz, O., S. Goebbels, M. Shamsadini Motlagh, G. Gerzabek:
> "Power Line Detection in Point Clouds with Point-SAM and RANSAC."
> accepted for The International Conference on Computer Vision Theory
> and Applications (VISAPP) (2027)
> https://doi.org/10.48550/arXiv.2611.21438
