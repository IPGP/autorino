## Installation

### create docker group
```
sudo addgroup --system docker
sudo adduser $USER docker
newgrp docker
```

### clone
```
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
docker run --rm -v "$(pwd):/data" trm2rinex:cli-light data/MAGC320b.2021.rt27 data/out
```
## Issues

### Issue about removing folders
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

