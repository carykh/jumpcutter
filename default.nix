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
      name = "pytube-9.5.0";
      src = pkgs.fetchurl { url = "https://files.pythonhosted.org/packages/5b/3a/76c9fa9d57224d0ba0de8f208c3ef4ef8b1d429c41c886f86eaee8ffd85e/pytube-9.5.0.tar.gz"; sha256 = "2a32f3475f063d25e7b7a7434a93b51d59aadbbda7ed24af48f097b2876c0964"; };
      doCheck = false;
      buildInputs = [];
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
    pytube
    audiotsm
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
      substituteInPlace $out/bin/jumpcutter --replace ffmpeg ${ffmpeg}/bin/ffmpeg
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
