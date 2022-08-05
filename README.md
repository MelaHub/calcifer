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

By running `poetry run calcifer` you'll get all the commands you can use. By running then `run calcifer <command> --help` you'll get how to run each command.

Availabel commands are
* audit-releases
* first-contribution
* issues-change-status-log: retrieve the list of status change of all Jira issues from a specific project created from a specific date
* issues-with-comments-by
* main-contributors
* unprotected-repos

Note that all repos caches results in a temporary file. By running the command, you'll get the name of the file the cache is saved to, and to refresh the cache at the moment you need to manually delete the file.