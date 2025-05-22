![](app/assets/frankenmsa_header.png)

Protein structure models like AlphaFold rely on Multiple Sequence Alignments (MSAs) for their prediction. Research has shown that the prediction of these models can be affected by manipulating the input MSAs, resulting in different conformations for the same target. To this end, we developed FrankenMSA, a small package designed to facilitate the workflow of manipulating MSAs. 

FrankenMSA offers a simple functional API to perform operations like:

- Filtering
- Slicing
- Cropping
- Clustering

Built to rely only on a Pandas Dataframe with a "sequence" column the package is designed for minimal requirements and maximal user freedom and compatibility with other scientific software. 

### Not a coder? - No problem!
We developed a graphical user interface using Dash to provide a clean and streamlined experience also to researchers who never wrote a line of code in their life. While the app naturally limits the functionality to some degree we worked hard to incorporate as much flexibility into it as possible. Are you missing something? Let us know! 

The app can be launched 
