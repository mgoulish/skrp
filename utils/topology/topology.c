#include <dirent.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>



#define MAX_NAME         50
#define MAX_CONNECTORS   12
#define MAX_ROUTERS      100


typedef
struct router_s
{
  char name[MAX_NAME];
  int amqp_listener_port;
  int tcp_pistener_port;
  int connector_ports[MAX_CONNECTORS];
  int n_connections;
}
router_t,
* router_p;


typedef
struct topology_s
{
  char     name    [ MAX_NAME ];
  router_t routers [ MAX_ROUTERS ];
  int      n_routers;
}
topology_t,
* topology_p;



// Connect A to B.
void
connect ( topology_p top, int a, int b )
{
  router_p router_a,
           router_b;

  router_a = top->routers + a;
  router_b = top->routers + b;

  if ( router_a->n_connections >= MAX_CONNECTORS )
  {
    fprintf ( stderr, "Too many connections.\n" );
    exit ( 1 );
  }

  // Router A needs to connect to Router B.
  // What is Router B's listening port?
  int listener_port = router_b->amqp_listener_port;

  // Now add that to A's list of connections to make.
  router_a->connector_ports [ router_a->n_connections ] = listener_port;
  router_a->n_connections ++;
}



void
mesh ( topology_p top, int size, int amqp_listen_port )
{
  top->n_routers = size;

  sprintf ( top->name, "%d_ring", top->n_routers );

  // Make router names and set AMQP listen ports.
  for ( int i = 0; i < top->n_routers; ++ i )
  {
    router_p router = top->routers + i;
    router->n_connections = 0;
    sprintf ( router->name, "router_%d", i );
    router->amqp_listener_port = amqp_listen_port + i;
  }

  // Make the connections.
}



void
ring ( topology_p top, int size, int amqp_listen_port )
{
  top->n_routers = size;

  sprintf ( top->name, "%d_ring", top->n_routers );

  // Make router names and set AMQP listen ports.
  for ( int i = 0; i < top->n_routers; ++ i )
  {
    router_p router = top->routers + i;
    router->n_connections = 0;
    sprintf ( router->name, "router_%d", i );
    router->amqp_listener_port = amqp_listen_port + i;
  }

  // Make the connection pattern.
  for ( int i = 0; i < top->n_routers; ++ i )
  {
    int connect_to = (i + 1) % size;
    connect ( top, i, connect_to );
  }
}



void
write_topology ( topology_p top )
{
  struct stat st = {0};

  if ( stat ( top->name, & st ) == -1) 
  {
    mkdir ( top->name, 0700);
  }
  else
  {
    fprintf ( stderr, "Dir |%s| already exists.\n", top->name );
    exit ( 1 );
  }

  for ( int i = 0; i < top->n_routers; ++ i )
  {
    router_p router = top->routers + i;

    char file_name[100];
    sprintf ( file_name, "./%s/%s.conf", top->name, router->name );

    FILE * fp = fopen ( file_name, "w" );
    fprintf ( fp, "router {\n" );
    fprintf ( fp, "  mode: interior\n" );
    fprintf ( fp, "  id: %s\n", router->name );
    fprintf ( fp, "}\n\n" );

    fprintf ( fp, "listener {\n" );
    fprintf ( fp, "  stripAnnotations: no\n" );
    fprintf ( fp, "  idleTimeoutSeconds: 120\n" );
    fprintf ( fp, "  saslMechanisms: ANONYMOUS\n" );
    fprintf ( fp, "  host: 0.0.0.0\n" );
    fprintf ( fp, "  role: inter-router\n" );
    fprintf ( fp, "  authenticatePeer: no\n" );
    fprintf ( fp, "  port: %d\n", router->amqp_listener_port  );
    fprintf ( fp, "}\n\n" );

    // Now do all the connectors.
    for ( int j = 0; j < router->n_connections; ++ j )
    {
      fprintf ( fp, "connector {\n" );
      fprintf ( fp, "  stripAnnotations: no\n" );
      fprintf ( fp, "  idleTimeoutSeconds: 120\n" );
      fprintf ( fp, "  saslMechanisms: ANONYMOUS\n" );
      fprintf ( fp, "  host: 127.0.0.1\n" );
      fprintf ( fp, "  role: inter-router\n" );
      fprintf ( fp, "  port: %d\n", router->connector_ports[j] );
      fprintf ( fp, "}\n" );
    }
    fclose ( fp );

    // Make the run script for this router.
    sprintf ( file_name, "./%s/%s_run.sh", top->name, router->name );
    fp = fopen ( file_name, "w" );
    fprintf ( fp, "#! /bin/bash\n\n" );
    fprintf ( fp, "sleep_until_minute\n\n" );
    fprintf ( fp, "# Start the router ------------------------------\n" );
    fprintf ( fp, "source ../../../utils/set_up_environment\n" );
    fprintf ( fp, "${ROUTER} --config ./%s.conf\n\n", router->name );
    fclose ( fp );
  }

  // Make the grand run script.
  char file_name[100];
  sprintf ( file_name, "./%s/r", top->name);
  FILE * fp = fopen ( file_name, "w" );
  fprintf ( fp, "#! /bin/bash\n\n" );
  for ( int i = 0; i < top->n_routers; ++ i )
  {
    router_p router = top->routers + i;
    fprintf ( fp, "./%s_run.sh &\n", router->name );
  }
  fprintf ( fp, "\n" );
  fclose ( fp );
}



int
main ( int argc, char ** argv )
{
  topology_t topology;

  ring      ( & topology, 100, 20000 );
  write_topology ( & topology );
}



