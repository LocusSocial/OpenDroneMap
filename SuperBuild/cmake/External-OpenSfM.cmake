set(_proj_name opensfm)
set(_SB_BINARY_DIR "${SB_BINARY_DIR}/${_proj_name}")

ExternalProject_Add(${_proj_name}
  DEPENDS           ceres opencv opengv
  PREFIX            ${_SB_BINARY_DIR}
  TMP_DIR           ${_SB_BINARY_DIR}/tmp
  STAMP_DIR         ${_SB_BINARY_DIR}/stamp
  #--Download step--------------
  DOWNLOAD_DIR      ${SB_DOWNLOAD_DIR}
  #URL               https://github.com/mapillary/OpenSfM/archive/odm-4.zip
  #URL_MD5           C7444B8595AAE33C6E191D8E8518BD5E
  URL               https://github.com/mapillary/OpenSfM/archive/v0.1.0.zip
  URL_MD5           7C62942DC61CBE937580E1F26CFA8025
  #URL               https://github.com/mapillary/OpenSfM/archive/master.zip
  #URL_MD5           0F1478F4A152ED6553F1F94A9D6CA0AE
  #--Update/Patch step----------
  UPDATE_COMMAND    ""
  #--Configure step-------------
  SOURCE_DIR        ${SB_SOURCE_DIR}/${_proj_name}
  CONFIGURE_COMMAND cmake <SOURCE_DIR>/${_proj_name}/src
    -DCERES_ROOT_DIR=${SB_INSTALL_DIR}
    -DOpenCV_DIR=${SB_INSTALL_DIR}/share/OpenCV
    -DOPENSFM_BUILD_TESTS=off

  #--Build step-----------------
  BINARY_DIR        ${_SB_BINARY_DIR}
  #--Install step---------------
  INSTALL_COMMAND    ""
  #--Output logging-------------
  LOG_DOWNLOAD      OFF
  LOG_CONFIGURE     OFF
  LOG_BUILD         OFF
)

