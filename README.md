## Script for merging anime in one mkv container.

Consumes fonts, subtitles, voice acting.

Video should be in `.mkv`, all files should have common pattern of naming i.e.
* Dandadan 01.tff
* Dandadan_XXX - 01.mka
* Dandadan_01.mkv etc

`inputPath` of folder with source files and `outputPath` of dto should be set in `merge.py` file

If source files located in different folders - script will copy them to the root of `inputPath`, process to `outputPath` and delete copied files.