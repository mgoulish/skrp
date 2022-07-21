#include <netinet/in.h>
#include <netinet/tcp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>


void 
error ( const char * msg )
{
  perror ( msg );
  exit ( 1 );
}


static
double
get_timestamp ( void )
{
  struct timeval t;
  gettimeofday ( & t, 0 );
  return t.tv_sec + ((double) t.tv_usec) / 1000000.0;
}


int 
main ( int argc, char ** argv )
{
  int listen_socket_fd, 
      data_socket_fd, 
      port;
  int n_messages,
      report_frequency;
  socklen_t client_address_length;
  struct sockaddr_in serv_addr, client_address;
  char name[200];
  sprintf ( name, "server_%d", getpid() );

  if ( argc < 3 ) 
  {
    fprintf(stderr,"usage %s hostname port n_messages\n", argv[0]);
    exit(1);
  }

  fprintf ( stderr, "%s : starting\n", name );

  port             = atoi(argv[1]);
  n_messages       = atoi(argv[2]);
  report_frequency = atoi(argv[3]);

  client_address_length = sizeof ( client_address );
  listen_socket_fd = socket ( AF_INET, SOCK_STREAM, 0 );
  if ( listen_socket_fd < 0 ) 
  {
    error ( strcat ( name, " : error opening socket") );
  }

  bzero ( (char *) & serv_addr, sizeof(serv_addr) );
  serv_addr.sin_family      = AF_INET;
  serv_addr.sin_addr.s_addr = INADDR_ANY;
  serv_addr.sin_port        = htons ( port );
  if ( 0 > bind ( listen_socket_fd, 
                  (struct sockaddr *) & serv_addr,
                  sizeof(serv_addr)
                )
     ) 
    error ( strcat ( name, " : error on binding" ));


  int count = 0;
  double start = get_timestamp();
  while ( count < n_messages )
  {
    // NOTE! Using the SOMAXCONN flag here nearly 
    // tripled my peer-to-peer connection speed.
    listen ( listen_socket_fd, SOMAXCONN );
    data_socket_fd = accept ( listen_socket_fd, 
                              (struct sockaddr *) & client_address, 
                              & client_address_length
                            );
    if ( data_socket_fd < 0 ) 
      error ( strcat ( name, " : error on accept"));

    // We have successfully made a new connection.
    // Now immediately close it, and count it.
    close ( data_socket_fd );
    count ++;

    if ( report_frequency > 0 )
    {
      if (! (count % report_frequency) )
      {
        double duration  = get_timestamp() - start;
        fprintf ( stderr, 
                  "%s : %d connections at %.6lf seconds\n", 
                  name,
                  count, 
                  duration
                );
      }
    }
  }
  close ( listen_socket_fd );

  if ( report_frequency > 0 )
  {
    double stop = get_timestamp();
    double dur  = stop - start;
    double cps = (double)count / dur;
    fprintf ( stderr, "%s : %.1lf connections per second\n", name, cps);
  }

  return 0; 
}



