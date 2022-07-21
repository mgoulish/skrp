package main

import ( 
         "fmt"
         "io"
         "net"
         "os"
         "time"
       )



var fp = fmt.Fprintf




func cnx_handler ( my_name    string,
                   cnx_number int, 
                   cnx        net.Conn ) {

  buffer := make ( []byte, 5000 )
  total_bytes := 0

  for {
    var   n   int
    var err error

    n, err = cnx.Read ( buffer )

    if err != nil {
      if err != io.EOF {
        fp ( os.Stderr, "%s error : connection read : |%s|\n", my_name, err.Error() )
      }
      break
    }

    if n > 0 {
      message := string(buffer[0:n])
      fp ( os.Stdout, "%s : received from cnx %d : |%s|\n", my_name, cnx_number, message )
      total_bytes += len ( message )
      fp ( os.Stdout, "%s has received %d total bytes.\n", my_name, total_bytes )
    }
  }
}





// This can accept multiple connections, and will 
// launch a goroutine for each.
func listen ( my_name string, my_addr, port string ) {
  cnx_count := 0

  tcp_listener, err := net.Listen ( "tcp", my_addr + ":" + port )
  if err != nil {
    fp ( os.Stdout, "%s error : net.Listen error |%s|\n", my_name, err.Error() )
    os.Exit ( 1 )
  }

  for {
    cnx, err := tcp_listener.Accept ( )

    if err != nil {
      fp ( os.Stdout, "%s error : |%s|\n", my_name, err.Error() )
      os.Exit(1)
    }
    fp ( os.Stdout, "accept returned.\n" )

    cnx_count ++
    go cnx_handler ( my_name, cnx_count, cnx )
  }
}





func dialer ( my_name string, other_addr, other_port string, timeout_seconds int ) ( cnx net.Conn, err error ) {

  for t := 0; t < timeout_seconds; t ++ {
    cnx, err := net.Dial ( "tcp", other_addr + ":" + other_port )
    if err == nil {
      return cnx, nil
    }

    fp ( os.Stdout, "dialer: |%s|\n", err.Error() )
    time.Sleep ( 2 * time.Second )
  }

  return nil, fmt.Errorf ( "%s : timed out", my_name )
}





func make_connection ( my_name string, n_messages int, other_addr, other_port string ) {

  cnx, err := dialer ( my_name, other_addr, other_port, 20 )

  if err != nil {
    fp ( os.Stdout, "%s error: |%s|\n", my_name, err.Error() )
    os.Exit ( 1 )
  }

  if cnx == nil {
    fp ( os.Stdout, "%s error : nil connection.\n", my_name )
    os.Exit ( 2 )
  }

  defer cnx.Close ( )

  message := make([]byte, 5000)
  for i := 0; i < 5000; i ++ {
    message[i] = 0
  }
  length := len(message)
  total_bytes_sent := 0

  for i := 0; i < n_messages; i ++ {
    fp ( cnx, string(message) )
    total_bytes_sent += length
    fp ( os.Stdout, "%s sent |%s|  total bytes sent: %d\n", 
         my_name, message, total_bytes_sent )
    time.Sleep ( 3 * time.Second )
  }

  fp ( os.Stdout, "%s is done sending.\n", my_name )
}





func main ( ) {
  my_name      := os.Args[1]
  other_addr   := os.Args[2]
  other_port   := os.Args[3]

  n_messages := 100
  go make_connection ( my_name, n_messages, other_addr, other_port )

  for {
    time.Sleep ( 1000 * time.Second )
  }
}





