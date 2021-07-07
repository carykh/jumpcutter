with import <nixpkgs> {};

let 
  python = python2;
  audiotsm = python.pkgs.buildPythonPackage {
    name = "audiotsm-0.1.2";
    src = pkgs.fetchurl { url = "https://files.pythonhosted.org/packages/f8/b8/721a9c613641c938a6fb9c7c3efb173b7f77b519de066e9cd2eeb27c3289/audiotsm-0.1.2.tar.gz"; sha256 = "8870af28fad0a76cac1d2bb2b55e7eac6ad5d1ad5416293eb16120dece6c0281"; };
    doCheck = false;
    buildInputs = [];
    propagatedBuildInputs = [
      python.pkgs.numpy
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "https://github.com/Muges/audiotsm";
      license = licenses.mit;
      description = "A real-time audio time-scale modification library";
    };
  };
  pytube = python.pkgs.buildPythonPackage {
    name = "pytube-9.4.0";
    src = pkgs.fetchurl { url = "https://files.pythonhosted.org/packages/db/59/f8b9e64a7ab420c3a91722f8d34a452013f59100fed4d8e930afa1da01f8/pytube-9.4.0.tar.gz"; sha256 = "686fe7ff6f2cb08828f1015f244c69e3a2ea85c8b6d727abe63ec5bfd17e58d2"; };
    doCheck = false;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "https://github.com/nficano/pytube";
      license = licenses.mit;
      description = "A pythonic library for downloading YouTube Videos.";
    };
  };

  pythonForThis = python.withPackages (ps: with ps;[
    scipy
    numpy
    pillow
    audiotsm
    pytube
  ]);
  jumpcutter = stdenv.mkDerivation {
    pname = "jumpcutter";
    version = "0.0.1";
    src = ./.;
    buildInputs = [
      pythonForThis
      ffmpeg
    ];
    installPhase = ''
      mkdir -p $out/bin
      echo "#!${pythonForThis}/bin/python" > $out/bin/jumpcutter
      cat $src/jumpcutter.py >> $out/bin/jumpcutter
      substituteInPlace $out/bin/jumpcutter --replace ffmpeg ${ffmpeg}
      chmod +x $out/bin/jumpcutter
    '';
  };
  
  nix-bundle-src = builtins.fetchGit {
    url = "https://github.com/matthewbauer/nix-bundle";
    rev = "113d8c6b426b0932a64c58c21cd065baad4c2314";
  };
  nix-bundle = (import ("${nix-bundle-src}/appimage-top.nix") {}) // (import "${nix-bundle-src}/default.nix" {});
in
  jumpcutter // {
    bundle = nix-bundle.nix-bootstrap {
      extraTargets = [];
      target = jumpcutter;
      run = "/bin/jumpcutter";
    };
  }
