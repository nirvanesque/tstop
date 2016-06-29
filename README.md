#TSTOP
This project contains the source code for the time-series topology data analysis framework and datasets for time-series characterization and classification as described in the paper:

Seversky, Lee M., Shelby Davis, and Matthew Berger. 
"On Time-Series Topological Data Analysis: New Data and Opportunities." 
Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition Workshops. 2016.


If you use the software or associated data please use the following citation:

```
@InProceedings{Seversky_2016_CVPR_Workshops,
author = {Seversky, Lee M. and Davis, Shelby and Berger, Matthew},
title = {On Time-Series Topological Data Analysis: New Data and Opportunities},
booktitle = {The IEEE Conference on Computer Vision and Pattern Recognition (CVPR) Workshops},
month = {June},
year = {2016}
}
```

# Installation

## Exterior Sources to be downloaded:

From Arnur Nigmetov (Graz Unvirsity of Technology, Graz, Austria)

Download
[geom_bottleneck](https://bitbucket.org/grey_narn/geom_bottleneck/downloads)
and extract to `tstop/ext/geom_dist/bottleneck` 

Download
[geom_matching](https://bitbucket.org/grey_narn/geom_matching/downloads)
and extract to `tstop/ext/geom_dist/wasserstein`

From David M. Mount and Sunil Arya (University of Maryland, College Park, Maryland)

Download [ANN](http://www.cs.umd.edu/~mount/ANN/) and extract to `tstop/ext/ANN`

## Building

Install [boost](http://www.boost.org) python and serialization libraries,
[scikit-learn](http://scikit-learn.org/stable/install.html),
[matplotlib](http://matplotlib.org/), and

On machines with `apt-get`:
```sh
$ sudo apt-get install libboost-python-dev libboost-serialization-dev python-matplotlib python-sklearn
```


Run in `tstop`
```sh
$ cmake -DCMAKE_BUILD_TYPE=release .
$ make 
```

# Running

Add `tstop/python` to the `PYTHONPATH` environment variable 

# Documentation and Tutorial

Documentation: `tstop/python/persistence/README.md`

Tutorial:`tstop/python/persistence/tutorial.md`