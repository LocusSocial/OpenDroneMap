#!/bin/sh

start_sec=$(ruby -e 'puts (Time.now.to_f).to_i')

rm -f *.png

# run opendronemap to generate map
for ((i=1; i<5; i++)); do
    cd office-4-tiles_$i

    rm -rf tiles/
    rm -rf odm_*

	docker run -it --rm -v $(pwd):/code/images -v $(pwd)/odm_orthophoto:/code/odm_orthophoto -v $(pwd)/odm_texturing:/code/odm_texturing -v $(pwd)/odm_georeferencing:/code/odm_georeferencing locus/opendronemap --mesh-octree-depth 8 --texturing-skip-visibility-test --opensfm-processes 5 --mesh-solver-divide 4
    gdal2tiles.py odm_orthophoto/odm_orthophoto.tif tiles
    
    cd ..
done

end_sec=$(ruby -e 'puts (Time.now.to_f).to_i')
elapsed_sec=$((end_sec - start_sec))
echo "----- Map generation took $elapsed_sec seconds -----"

# crop the orthophoto to TMS tiles
for ((i=1; i<5; i++)); do
    cd office-4-tiles_$i
    gdal2tiles.py odm_orthophoto/odm_orthophoto.tif tiles
    cd ..
done

cp office-4-tiles_1/tiles/18/74729/161839.png 0.png
cp office-4-tiles_2/tiles/18/74730/161839.png 1.png
cp office-4-tiles_3/tiles/18/74729/161838.png 2.png
cp office-4-tiles_4/tiles/18/74730/161838.png 3.png

