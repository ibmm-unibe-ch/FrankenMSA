![](app/assets/frankenmsa_header.png)

Protein structure models like AlphaFold rely on Multiple Sequence Alignments (MSAs) for their prediction. Research has shown that the prediction of these models can be affected by manipulating the input MSAs, resulting in different conformations for the same target. To this end, we developed FrankenMSA, a small package designed to facilitate the workflow of manipulating MSAs. 

FrankenMSA offers a simple functional API to perform operations like:

- Filtering
- Slicing
- Cropping
- Clustering

Built to rely only on a Pandas Dataframe with a "sequence" column the package is designed for minimal requirements and maximal user freedom and compatibility with other scientific software. 

### Not a coder? - No problem!
<a href="https://colab.research.google.com/github/ibmm-unibe-ch/FrankenMSA/blob/dev/app/FrankenMSA_app_colab.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

We developed a graphical user interface using Dash to provide a clean and streamlined experience also to researchers who never wrote a line of code in their life. While the app naturally limits the functionality to some degree we worked hard to incorporate as much flexibility into it as possible. Are you missing something? Let us know! 

To launch the app just hit the "Open in Colab button above". A CPU runtime will suffice.

> Dash is known to have issues on Safari so it is recommended to use another browser like Chrome instead!



