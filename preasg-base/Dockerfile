FROM cern/slc6-base
RUN mkdir /code
WORKDIR /code
RUN rpm --import http://emisoft.web.cern.ch/emisoft/dist/EMI/3/RPM-GPG-KEY-emi
RUN curl -o /etc/yum.repos.d/egi-trustanchors.repo \
            http://repository.egi.eu/sw/production/cas/1/current/repo-files/egi-trustanchors.repo
RUN yum --nogpgcheck -y install yum-priorities yum-protectbase ca-policy-egi-core
RUN curl -O http://emisoft.web.cern.ch/emisoft/dist/EMI/3/sl6/x86_64/base/emi-release-3.0.0-2.el6.noarch.rpm && \
    yum localinstall -y emi-release-3.0.0-2.el6.noarch.rpm
RUN yum install -y voms-clients3 globus-proxy-utils

RUN mkdir -p /etc/grid-security/vomsdir/atlas
ADD lcg-voms2.cern.ch.lsc /etc/grid-security/vomsdir/atlas/lcg-voms2.cern.ch.lsc
ADD voms2.cern.ch.lsc /etc/grid-security/vomsdir/atlas/voms2.cern.ch.lsc

RUN mkdir -p /etc/vomses
ADD atlas-lcg-voms2.cern.ch /etc/vomses/atlas-lcg-voms2.cern.ch
ADD atlas-lcg-voms2.cern.ch /etc/vomses/atlas-voms2.cern.ch

RUN yum install -y git tar
RUN git clone git://github.com/PanDAWMS/panda-client.git && \
    cd panda-client && python setup.py install
ENV PATHENA_GRID_SETUP_SH /dev/null
WORKDIR /
RUN rm -rf /code
