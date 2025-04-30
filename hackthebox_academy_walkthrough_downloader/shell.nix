{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "htb-academy-walkthrough-downloader";
  buildInputs = [
    pkgs.python311
    pkgs.python311Packages.requests
    pkgs.python311Packages.brotli
    pkgs.python311Packages.urllib3
  ];
  shellHook = ''
    echo "Ready to download internet points."
  '';
}