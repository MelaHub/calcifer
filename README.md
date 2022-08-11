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
* github: all commands here use unarchived repos
** backstage-missing: retrieves all repos that do not have a catalog-info.yaml in the main branch
** commits-with-tag: retrieves the list of commits across al repos with a specific tag; if you use a release tag this can be used to extract all releases
** empty_repos: retrieves all repos with no commits
** first-contribution: retrieves for all the people contributing to an org the very first contribution
** top-contributors: retrieves the top contributors for each repo in an org
** unprotected-repos: retrieves all repos not protected in an org
* jira
** issues-change-status-log: retrieves the list of status change of all Jira issues from a specific project created from a specific date
** issues-with-comments-by: retrieves the list of issues that had at least one comment from a specific person

Note that all repos caches results in a temporary file. By running the command, you'll get the name of the file the cache is saved to, and to refresh the cache at the moment you need to manually delete the file.