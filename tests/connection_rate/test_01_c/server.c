#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h> 
#include <sys/socket.h>
#include <netinet/tcp.h>
#include <netinet/in.h>

void 
error ( const char * msg )
{
  perror ( msg );
  exit ( 1 );
}


int 
main ( int argc, char ** argv )
{
  int listen_socket_fd, 
      data_socket_fd, 
      port;
  int n;
  socklen_t client_address_length;
  struct sockaddr_in serv_addr, client_address;

  if ( argc < 3 ) 
  {
    fprintf(stderr,"usage %s hostname port n_messages\n", argv[0]);
    exit(1);
  }

  fprintf ( stderr, "server : starting\n" );

  port = atoi(argv[1]);
  n    = atoi(argv[2]);

  client_address_length = sizeof ( client_address );
  listen_socket_fd = socket ( AF_INET, SOCK_STREAM, 0 );
  if ( listen_socket_fd < 0 ) 
    error ( "server : error opening socket" );

  /*
  No help.
  int one = 1;
  setsockopt ( listen_socket_fd, 
               IPPROTO_TCP, 
               TCP_QUICKACK, 
               & one, 
               sizeof(one)
             );
  */

  bzero ( (char *) & serv_addr, sizeof(serv_addr) );
  serv_addr.sin_family      = AF_INET;
  serv_addr.sin_addr.s_addr = INADDR_ANY;
  serv_addr.sin_port        = htons ( port );
  if ( 0 > bind ( listen_socket_fd, 
                  (struct sockaddr *) & serv_addr,
                  sizeof(serv_addr)
                )
     ) 
    error ( "server : error on binding" );


  int count = 0;
  while ( count < n )
  {
    // NOTE! Using the SOMAXCONN flag here nearly 
    // tripled my peer-to-peer connection speed.
    listen ( listen_socket_fd, SOMAXCONN );
    data_socket_fd = accept ( listen_socket_fd, 
                              (struct sockaddr *) & client_address, 
                              & client_address_length
                            );
    /*
    No help.
    one = 1;
    setsockopt ( data_socket_fd, 
                 IPPROTO_TCP, 
                 TCP_QUICKACK, 
                 & one, 
                 sizeof(one)
               );
    */
    if ( data_socket_fd < 0 ) 
      error("server : error on accept");

    // We have successfully made a new connection.
    // Now immediately close it, and count it.
    close ( data_socket_fd );
    count ++;
  }

  close ( listen_socket_fd );

  fprintf ( stderr, "server : exiting after %d connections.\n", count );
  return 0; 
}



