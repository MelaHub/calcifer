# calcifer

A Python tool to fetch stats across all repos within an org.

                                       /                                       
                                     */     ,                                   
                                   /// .      /                                 
                               * ./////*      /                                 
                                *//////////      /                              
                      /     //  ////////////   *// *                            
                     ///   /////////////////   .////                            
                  /.      /////////,//,/////  ./////////                        
                   ///    ////////,*/,,,/////////////////   /   ,               
                   ////   //////*,,,*,,,,////,,,,/////////  *//                 
                * ,////* //////,,,,,,,,,,///,,,,,,,///////  //                  
               / *///////////*,,,,,,,,,,.,,,,,,,,,,,/,,///  ///                 
                 ///////,///,,,,,,.,,,,,..,.,,,,,,,,,,,/////////  ,             
                 //////*,,,,,,,,,.....,........,,,,,,,,///,,,,///  /  ,         
              /  *////,,,,,,,,,..................,,,,,,,,,,,,,,///  /           
             //   ///,,,,,,,,,....................     ,,,,,,,,///              
            ////////,,,,,*      *............... .%%    (,,,,,*///    *         
            ////////,,,,     %%  %............./         /,,,,///  //           
            //////,,,,,*         ..............%         ,,,*////////           
            /////,,,,,,,%       (................%    %,,,,,,,,/////            
             ////,,,,,,,..................,,,,,,,,,,..,,,,,,,,/////&/.   

## How to

`poetry run calcifer <command> --github-org <orgname> --out-file-path <fullpath> --github-user <githubuser> --github-token <githubtoken>`

## Prod release audit

The output is a CSV file with all releases done in 2021.

`poetry run calcifer audit-releases --github-org <orgname> --out-file-path <fullpath> --github-user <githubuser> --github-token <githubtoken>`

## Top contributors

The output is a CSV file with the top n contributors from the same org, with n defaulted to 3 or set via --n-contrib.

`poetry run calcifer main-contributions --github-org <orgname> --out-file-path <fullpath> --github-user <githubuser> --github-token <githubtoken>`

## First contribution

`poetry run calcifer first-contribution --github-org <orgname> --out-file-path <fullpath> --github-user <githubuser> --github-token <githubtoken>`
  
