FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN wget --quiet \
      -c 'https://github.com/openshift/origin/releases/download/v3.11.0/openshift-origin-server-v3.11.0-0cbc58b-linux-64bit.tar.gz' \
      -O openshift.tgz

# O segredo para extrair o arquivo sem o aminho é --strip-components 1
RUN tar -xf openshift.tgz \
      --strip-components 1 \
      -C /usr/bin/ \
      openshift-origin-server-v3.11.0-0cbc58b-linux-64bit/oc 2>/dev/null

RUN tar -xf openshift.tgz \
      --strip-components 1 \
      -C /usr/bin/ \
      openshift-origin-server-v3.11.0-0cbc58b-linux-64bit/kubectl 2>/dev/null

RUN chmod +x /usr/bin/oc /usr/bin/kubectl

RUN rm -f openshift.tgz

COPY top-pods-dot-net.py .

ENV PYTHONUNBUFFERED=0

EXPOSE 8000

CMD [ "python","-u","./top-pods-dot-net.py" ]
