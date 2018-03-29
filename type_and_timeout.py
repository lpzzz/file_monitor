from threading import Thread
def input_func( context ):
    context[ 'data' ] = input( 'input:' )
context = { 'data' : 'default' }
t = Thread( target = input_func ,args = ( context , ) )
t.daemon = True
t.start( )
t.join(10)
print( context )