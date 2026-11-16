set(MODULE_NAME PulmoSlicerAI)

set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  PulmoSlicerAILib/__init__.py
  PulmoSlicerAILib/progress.py
  PulmoSlicerAILib/progress_panel.py
  PulmoSlicerAILib/ptl_setup.py
  PulmoSlicerAILib/workflow.py
  PulmoSlicerAILib/html_export_panel.py
  PulmoSlicerAILib/html_export/__init__.py
  PulmoSlicerAILib/html_export/anatomy.py
  PulmoSlicerAILib/html_export/color_templates.py
  PulmoSlicerAILib/html_export/contracts.py
  PulmoSlicerAILib/html_export/exporter.py
  PulmoSlicerAILib/html_export/html_writer.py
  PulmoSlicerAILib/html_export/mesh_codec.py
  PulmoSlicerAILib/html_export/mesh_pipeline.py
  PulmoSlicerAILib/html_export/privacy.py
  )

set(MODULE_PYTHON_RESOURCES
  PulmoSlicerAILib/html_export/assets/viewer.css
  PulmoSlicerAILib/html_export/assets/viewer_bundle.js
  PulmoSlicerAILib/html_export/assets/THIRD_PARTY_NOTICES.txt
  )

slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

install(
  DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/../../pulmoslicer_engine
  DESTINATION ${Slicer_INSTALL_QTSCRIPTEDMODULES_LIB_DIR}
  PATTERN "__pycache__" EXCLUDE
  PATTERN "*.pyc" EXCLUDE
  )

