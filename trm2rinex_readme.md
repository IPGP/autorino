## Installation

### Prerequise: install Docker (on your Ubuntu)
```
https://www.simplilearn.com/tutorials/docker-tutorial/how-to-install-docker-on-ubuntu
```
### create docker group
```
sudo addgroup --system docker
sudo adduser $USER docker
newgrp docker
```

### clone
```
cd $HOME/your/favorite/folder
git clone https://github.com/Matioupi/trm/trm2rinex-docker
```
### build
```
cd trm2rinex-docker
docker build -t trm2rinex:cli-light .
```
running it in *sudo* mode might be better

### clean useless Docker images
at the end of the installation
```
docker image ls
```
and remove intermediate images
```
docker image rm 925d947bf045
```

## Usage

### Run the test file conversion
```
cd <...>/trm2rinex-docker
docker run --rm -v "$(pwd):/data" trm2rinex:cli-light data/MAGC320b.2021.rt27 -p data/out
```
## Issues
###
#### Error 
```
klein@zoisite:~/SOFT/trm2rinex-docker$ docker run --rm -v "$(pwd):/data" trm2rinex:cli-light data/MAGC320b.2021.rt27 data/out
Scanning data/MAGC320b.2021.rt27...Complete!
Converting MAGC320b.2021.rt27...Error: CrinexFile - System.UnauthorizedAccessException: Access to the path "Z:\data\MAGC320b.2021.21n" is denied.
  at System.IO.FileStream..ctor (System.String path, System.IO.FileMode mode, System.IO.FileAccess access, System.IO.FileShare share, System.Int32 bufferSize, System.Boolean anonymous, System.IO.FileOptions options) [0x0019e] in <bee01833bcad4475a5c84b3c3d7e0cd6>:0 
  at System.IO.FileStream..ctor (System.String path, System.IO.FileMode mode, System.IO.FileAccess access, System.IO.FileShare share, System.Int32 bufferSize, System.IO.FileOptions options) [0x00000] in <bee01833bcad4475a5c84b3c3d7e0cd6>:0 
  at (wrapper remoting-invoke-with-check) System.IO.FileStream..ctor(string,System.IO.FileMode,System.IO.FileAccess,System.IO.FileShare,int,System.IO.FileOptions)
  at System.IO.StreamWriter..ctor (System.String path, System.Boolean append, System.Text.Encoding encoding, System.Int32 bufferSize) [0x00055] in <bee01833bcad4475a5c84b3c3d7e0cd6>:0 
  at System.IO.StreamWriter..ctor (System.String path, System.Boolean append) [0x00008] in <bee01833bcad4475a5c84b3c3d7e0cd6>:0 
  at (wrapper remoting-invoke-with-check) System.IO.StreamWriter..ctor(string,bool)
  at System.IO.File.CreateText (System.String path) [0x0000e] in <bee01833bcad4475a5c84b3c3d7e0cd6>:0 
  at trimble.rinex.CrinexFile..ctor (System.String inputFilePath, System.IO.FileMode mode) [0x00176] in <6b991ac620904a08a4ad53d3cafee6d1>:0 : Z:\data\MAGC320b.2021.21n using mode: Create
```
#### Solution


### Issue about removing folders during Docker compilation
#### Error
In the log, at the step 25/65, you have:
```
rm: cannot remove '/opt/wine/share/include/windows': Directory not empty
```
#### Solution
then in the *Dockerfile*, comment the lines 170-173:
```
RUN strip -s ${WINE_INSTALL_PREFIX}/lib/wine/i386-windows/* \
    && strip -s ${WINE_INSTALL_PREFIX}/lib/wine/i386-unix/* \
    && strip -s ${WINE_INSTALL_PREFIX}/bin/wine \
                ${WINE_INSTALL_PREFIX}/bin/wineserver \
                ${WINE_INSTALL_PREFIX}/bin/wine-preloader
#    && rm -rf ${WINE_INSTALL_PREFIX}/include \
#    && rm -rf ${WINE_INSTALL_PREFIX}/lib/wine/i386-unix/*.a \
#    && rm -rf ${WINE_INSTALL_PREFIX}/lib/wine/i386-windows/*.a \
#    && rm -rf ${WINE_INSTALL_PREFIX}/share/man
```

and lines 232-234:
```
USER root
COPY clean.sh /home/${USER_NAME}/clean.sh
RUN chmod 755 /home/${USER_NAME}/clean.sh
#RUN rm -rf /home/${USER_NAME}/.wine/drive_c/windows/Installer \
#    && rm -rf /tmp/* \
#    && /home/${USER_NAME}/clean.sh ${USER_NAME} ${WINE_INSTALL_PREFIX}
```


