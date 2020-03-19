mkdir tmp
cd tmp
wget https://bitbucket.org/dtsarkov/factplusplus/downloads/FaCTpp-OWLAPI-4.x-v1.6.5.jar
wget https://bitbucket.org/dtsarkov/factplusplus/downloads/FaCTpp-linux-v1.6.5.zip
unzip *.zip
cd ..

mkdir osp/core/java/lib
mkdir osp/core/java/lib/jars
mkdir osp/core/java/lib/so
mvn install:install-file -Dfile=tmp/FaCTpp-OWLAPI-4.x-v1.6.5.jar -DgroupId=uk.ac.manchester.cs \
    -DartifactId=factplusplus -Dversion=1.6.5 -Dpackaging=jar
mvn dependency:copy-dependencies -DoutputDirectory=lib/jars -Dhttps.protocols=TLSv1.2 -f osp/core/java/pom.xml
if [[ "$(uname -m)" ==  "x86_64" ]]
  then
    mv tmp/Fact++-linux-v1.6.5/64bit/* osp/core/java/lib/so
  else
    mv tmp/Fact++-linux-v1.6.5/64bit/* osp/core/java/lib/so
fi
rm -rf tmp
touch osp/core/java/target/__init__.py
touch osp/core/java/lib/__init__.py
touch osp/core/java/lib/so/__init__.py
touch osp/core/java/lib/jars/__init__.py