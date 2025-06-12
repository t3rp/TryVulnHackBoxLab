{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {

  # Hook
  shellHook = ''
    echo "Python: $(python3 --version)"
    echo "Usage: python3 pdf_gen.py [folder] -o [output.pdf]"
    echo "Ready to download internet points."
  '';

  # Packages
  buildInputs = with pkgs; [
    python3
    python3Packages.pip
    python3Packages.pillow
    python3Packages.ocrmypdf
    python3Packages.tqdm
    
    # OCR dependencies
    tesseract
    ghostscript
    poppler_utils
    qpdf
    
    # Image processing libraries
    libjpeg
    libpng
    libtiff
    libwebp
  ];
}