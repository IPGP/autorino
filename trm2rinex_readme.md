#### create docker group
sudo addgroup --system docker
sudo adduser $USER docker
newgrp docker

#### clone
```
git clone https://github.com/Matioupi/trm/trm2rinex-docker
```
#### build
```
cd trm2rinex-docker
docker build -t trm2rinex:cli-light .
```

#### Issue about removing folders
In the log, at the step 25/65, you have:
```
rm: cannot remove '/opt/wine/share/include/windows': Directory not empty
```
